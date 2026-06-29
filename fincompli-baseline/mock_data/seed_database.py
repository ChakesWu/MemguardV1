"""
Database Seed Script
數據庫種子腳本

Seeds all generated mock data into ChromaDB and SQLite databases.
將所有生成的模擬數據導入 ChromaDB 和 SQLite 數據庫。
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings, get_data_dir


class DatabaseSeeder:
    """Database Seeder"""

    def __init__(self):
        self.seeds_dir = Path(__file__).parent / "seeds"
        self.data_dir = get_data_dir()
        self.sqlite_path = self.data_dir / "sqlite" / "fincompli.db"
        self.chroma_path = self.data_dir / "chroma"
        
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        
        self.customers = []
        self.sar_cases = []
        self.regulations = []
        self.transactions = []

    def load_seed_files(self):
        print("=" * 70)
        print("  Loading Seed Files")
        print("=" * 70)
        
        customers_file = self.seeds_dir / "customers.json"
        if customers_file.exists():
            with open(customers_file, 'r', encoding='utf-8') as f:
                self.customers = json.load(f)
            print(f"  ✓ Loaded {len(self.customers)} customers")
        
        sar_file = self.seeds_dir / "sar_cases.json"
        if sar_file.exists():
            with open(sar_file, 'r', encoding='utf-8') as f:
                self.sar_cases = json.load(f)
            print(f"  ✓ Loaded {len(self.sar_cases)} SAR cases")
        
        regs_file = self.seeds_dir / "regulations.json"
        if regs_file.exists():
            with open(regs_file, 'r', encoding='utf-8') as f:
                self.regulations = json.load(f)
            print(f"  ✓ Loaded {len(self.regulations)} regulations")
        
        txn_file = self.seeds_dir / "transaction_scenarios.json"
        if txn_file.exists():
            with open(txn_file, 'r', encoding='utf-8') as f:
                self.transactions = json.load(f)
            print(f"  ✓ Loaded {len(self.transactions)} transaction scenarios")
        print()

    def create_sqlite_schema(self):
        print("=" * 70)
        print("  Creating SQLite Schema")
        print("=" * 70)
        
        conn = sqlite3.connect(str(self.sqlite_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                kyc_status TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                country TEXT NOT NULL,
                account_number TEXT NOT NULL,
                account_open_date TEXT NOT NULL,
                typical_transaction_min INTEGER,
                typical_transaction_max INTEGER,
                typical_countries TEXT,
                monthly_transaction_count INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Created customers table")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                customer_id TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL,
                scenario_type TEXT NOT NULL,
                expected_risk_score REAL,
                test_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Created transactions table")
        
        conn.commit()
        conn.close()
        print()

    def seed_sqlite(self):
        print("=" * 70)
        print("  Seeding SQLite Database")
        print("=" * 70)
        
        conn = sqlite3.connect(str(self.sqlite_path))
        cursor = conn.cursor()
        
        for customer in self.customers:
            cursor.execute("""
                INSERT OR REPLACE INTO customers (
                    customer_id, name, type, kyc_status, risk_level, country,
                    account_number, account_open_date, typical_transaction_min,
                    typical_transaction_max, typical_countries, monthly_transaction_count, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer['customer_id'], customer['name'], customer['type'],
                customer['kyc_status'], customer['risk_level'], customer['country'],
                customer['account_number'], customer['account_open_date'],
                customer['typical_transaction_range']['min'],
                customer['typical_transaction_range']['max'],
                json.dumps(customer['typical_countries']),
                customer['monthly_transaction_count'], customer['notes']
            ))
        print(f"  ✓ Inserted {len(self.customers)} customers")
        
        for txn in self.transactions:
            # Handle structuring: use related_transactions sum instead of direct amount/currency
            if 'amount' not in txn and 'related_transactions' in txn:
                related = txn['related_transactions']
                _amount = sum(r.get('amount', 0) for r in related)
                _currency = related[0].get('currency', 'HKD') if related else 'HKD'
            else:
                _amount = txn.get('amount', 0)
                _currency = txn.get('currency', 'HKD')

            cursor.execute("""
                INSERT OR REPLACE INTO transactions (
                    transaction_id, timestamp, customer_id, amount, currency,
                    scenario_type, expected_risk_score, test_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                txn['transaction_id'], txn['timestamp'], txn['customer_id'],
                _amount, _currency, txn['scenario_type'],
                txn.get('expected_risk_score'), txn.get('test_notes')
            ))
        print(f"  ✓ Inserted {len(self.transactions)} transactions")
        
        conn.commit()
        conn.close()
        print()

    def seed_chromadb(self):
        print("=" * 70)
        print("  Seeding ChromaDB")
        print("=" * 70)
        
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
        except ImportError:
            print("  ⚠️  chromadb not installed - skipping")
            return
        
        client = chromadb.PersistentClient(
            path=str(self.chroma_path),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        episodic = client.get_or_create_collection(name="episodic_memory")
        if len(self.sar_cases) > 0:
            episodic.upsert(
                ids=[c['sar_id'] for c in self.sar_cases],
                documents=[c['case_summary'] for c in self.sar_cases],
                metadatas=[{"case_type": c['case_type']} for c in self.sar_cases]
            )
            print(f"  ✓ Inserted {len(self.sar_cases)} SAR cases")
        
        semantic = client.get_or_create_collection(name="semantic_memory")
        if len(self.regulations) > 0:
            semantic.upsert(
                ids=[r['regulation_id'] for r in self.regulations],
                documents=[r['content'] for r in self.regulations],
                metadatas=[{"authority": r['authority']} for r in self.regulations]
            )
            print(f"  ✓ Inserted {len(self.regulations)} regulations")
        print()

    def run(self):
        print("\n" + "=" * 70)
        print("  FinCompli Database Seeder")
        print("=" * 70 + "\n")
        
        self.load_seed_files()
        self.create_sqlite_schema()
        self.seed_sqlite()
        self.seed_chromadb()
        
        print("=" * 70)
        print("  ✅ Database Seeding Complete!")
        print("=" * 70 + "\n")


def main():
    seeder = DatabaseSeeder()
    seeder.run()


if __name__ == "__main__":
    main()
