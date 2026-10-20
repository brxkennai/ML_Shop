"""Reproducible synthetic e-commerce data. Python standard library only."""
import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

START = datetime(2025, 1, 1)
END = datetime(2026, 9, 1)
CATEGORIES = ['electronics', 'fashion', 'beauty', 'home', 'sports', 'books', 'pets', 'other']
SOURCES = ['organic', 'ads', 'email', 'social', 'direct', 'referral']
DEVICES = ['mobile', 'desktop', 'tablet']
SEGMENTS = [
    ('low', 0.42, 0.015),
    ('mid', 0.43, 0.075),
    ('high', 0.15, 0.22),
]


def timestamp(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def random_dt(rng, start, end):
    return start + timedelta(seconds=rng.randrange(max(1, int((end-start).total_seconds()))))


def choose_segment(rng):
    x = rng.random()
    acc = 0.0
    for name, probability, conversion in SEGMENTS:
        acc += probability
        if x < acc:
            return name, conversion
    return 'high', 0.22


def main():
    parser = argparse.ArgumentParser(description='Create synthetic e-commerce CSV data')
    parser.add_argument('--users', type=int, default=2500, help='2500 pilot, 50000 full')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--out', type=Path, default=Path('data'))
    args = parser.parse_args()
    if args.users < 1:
        parser.error('--users must be positive')
    rng = random.Random(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    files = {}
    writers = {}
    fields = {
        'users': ['user_id', 'registered_at', 'country', 'acquisition_channel', 'age'],
        'sessions': ['session_id', 'user_id', 'started_at', 'device', 'traffic_source', 'duration_seconds'],
        'events': ['event_id', 'session_id', 'user_id', 'event_at', 'event_type', 'category'],
        'orders': ['order_id', 'user_id', 'session_id', 'created_at', 'amount', 'status'],
        'payments': ['payment_id', 'order_id', 'paid_at', 'amount', 'status', 'method'],
        'support_tickets': ['ticket_id', 'user_id', 'created_at', 'topic', 'status'],
    }
    counts = {table: 0 for table in fields}
    try:
        for table, columns in fields.items():
            f = (args.out / f'{table}.csv').open('w', encoding='utf-8', newline='')
            files[table] = f
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writers[table] = writer
        def write(table, **values):
            writers[table].writerow(values)
            counts[table] += 1

        session_id = event_id = order_id = payment_id = ticket_id = 0
        for user_id in range(1, args.users + 1):
            segment, conversion = choose_segment(rng)
            registered_at = random_dt(rng, datetime(2024, 9, 1), datetime(2025, 10, 1))
            age = '' if rng.random() < 0.06 else rng.randint(18, 75)
            write('users', user_id=user_id, registered_at=timestamp(registered_at),
                  country=rng.choices(['RU', 'KZ', 'BY', 'AM', 'OTHER'], [65, 14, 12, 4, 5])[0],
                  acquisition_channel=rng.choice(SOURCES), age=age)

            # Activity differs by latent user propensity. It makes the classification meaningful.
            mean = {'low': 5, 'mid': 9, 'high': 15}[segment]
            n_sessions = max(0, int(rng.gauss(mean, mean * 0.35)))
            activity_start = max(START, registered_at)
            for _ in range(n_sessions):
                started_at = random_dt(rng, activity_start, END - timedelta(hours=2))
                session_id += 1
                duration = rng.randint(25, 2400)
                source = rng.choices(SOURCES, [35, 20, 15, 10, 15, 5])[0]
                device = rng.choices(DEVICES, [68, 28, 4])[0]
                write('sessions', session_id=session_id, user_id=user_id,
                      started_at=timestamp(started_at), device=device,
                      traffic_source=source, duration_seconds=duration)
                n_events = rng.randint(3, 10)
                favorite_category = rng.choice(CATEGORIES)
                will_buy = rng.random() < conversion
                cart = rng.random() < (0.40 if will_buy else 0.08)
                event_types = ['page_view', 'product_view', 'search', 'page_view']
                if cart:
                    event_types += ['add_to_cart']
                if will_buy:
                    event_types += ['checkout']
                while len(event_types) < n_events:
                    event_types.append(rng.choice(['page_view', 'product_view', 'search']))
                rng.shuffle(event_types)
                for i, event_type in enumerate(event_types):
                    event_id += 1
                    event_at = started_at + timedelta(seconds=int(duration * (i + 1) / (len(event_types) + 1)))
                    category = '' if rng.random() < 0.035 else favorite_category
                    write('events', event_id=event_id, session_id=session_id, user_id=user_id,
                          event_at=timestamp(event_at), event_type=event_type, category=category)
                if will_buy:
                    order_id += 1
                    created_at = started_at + timedelta(seconds=duration + rng.randint(1, 600))
                    status = rng.choices(['completed', 'cancelled', 'refunded', 'pending'], [83, 9, 5, 3])[0]
                    amount = round(rng.lognormvariate(4.2, 0.85), 2)
                    if rng.random() < 0.003:
                        amount *= 100  # Intentional outlier
                    write('orders', order_id=order_id, user_id=user_id, session_id=session_id,
                          created_at=timestamp(created_at), amount=f'{amount:.2f}', status=status)
                    method = rng.choice(['card', 'sbp', 'wallet'])
                    if status == 'completed' and rng.random() < 0.035:
                        payment_id += 1
                        write('payments', payment_id=payment_id, order_id=order_id,
                              paid_at=timestamp(created_at + timedelta(minutes=1)),
                              amount=f'{amount:.2f}', status='failed', method=method)
                    payment_id += 1
                    if status in ('completed', 'refunded'):
                        p_status = 'success' if status == 'completed' else 'refunded'
                    else:
                        p_status = 'failed' if status == 'cancelled' else 'pending'
                    write('payments', payment_id=payment_id, order_id=order_id,
                          paid_at=timestamp(created_at + timedelta(minutes=rng.randint(2, 40))),
                          amount=f'{amount:.2f}', status=p_status, method=method)
            # Optional customer support interaction.
            if n_sessions and rng.random() < {'low': .08, 'mid': .16, 'high': .30}[segment]:
                ticket_id += 1
                created_at = random_dt(rng, activity_start, END)
                write('support_tickets', ticket_id=ticket_id, user_id=user_id,
                      created_at=timestamp(created_at),
                      topic=rng.choice(['delivery', 'refund', 'product', 'account', 'other']),
                      status=rng.choice(['open', 'closed', 'pending']))
            if user_id % 10000 == 0:
                print(f'Generated {user_id:,}/{args.users:,} users...')
    finally:
        for f in files.values():
            f.close()
    print('Finished:', args.out.resolve())
    for table, num in counts.items():
        print(f'  {table:16s} {num:,}')
    print('Synthetic data only. Do not treat patterns as real customer behavior.')


if __name__ == '__main__':
    main()
