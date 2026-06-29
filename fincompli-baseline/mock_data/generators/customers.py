"""
Customer Data Generator
客戶數據生成器

Generates 100 realistic virtual customers with proper risk categorization.
生成 100 個真實的虛擬客戶，並進行適當的風險分類。

Risk Distribution / 風險分佈:
- Low Risk (60): Local residents/businesses, stable transaction history, complete KYC
- Medium Risk (30): Offshore companies or recent accounts, incomplete documentation
- High Risk (10): PEP or FATF high-risk jurisdictions

[Business Purpose] Provides realistic customer profiles for compliance testing
[業務目的] 為合規測試提供真實的客戶檔案
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
import random
from typing import List, Dict
from faker import Faker

# Initialize Faker with English locale
fake = Faker('en_US')
Faker.seed(42)  # For reproducibility / 可重現性
random.seed(42)


class CustomerGenerator:
    """
    Customer Data Generator
    客戶數據生成器
    """

    def __init__(self):
        self.customer_id_counter = 1
        self.generated_customers: List[Dict] = []

    def _generate_account_number(self, country: str) -> str:
        """
        Generate realistic bank account number by country
        根據國家生成真實的銀行賬號
        """
        if country == "HK":
            return f"HK{random.randint(10, 99)} {random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}"
        elif country == "SG":
            return f"SG{random.randint(10, 99)} DBS{random.randint(1000, 9999)} {random.randint(10000, 99999)}"
        elif country == "KY":
            return f"KY{random.randint(1, 9)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
        elif country == "BVI":
            return f"BVI-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
        else:
            return f"{country}{random.randint(100000, 999999)}"

    def generate_low_risk_customer(self) -> Dict:
        """
        Generate low-risk customer profile
        生成低風險客戶檔案

        Characteristics: Local resident/business, long-term stable, complete KYC
        特徵：本地居民/企業，長期穩定，KYC 完整
        """
        customer_type = random.choice(["individual", "corporate"])
        country = random.choice(["HK", "SG"])

        if customer_type == "individual":
            name = fake.name()
            notes = f"Long-term retail banking customer, stable salary deposits and regular expenses"
        else:
            name = f"{fake.company()} Ltd"
            notes = f"Established local business, regular commercial transactions"

        account_open_date = datetime.now() - timedelta(days=random.randint(730, 3650))

        return {
            "customer_id": f"C-{self.customer_id_counter:05d}",
            "name": name,
            "type": customer_type,
            "kyc_status": "verified",
            "risk_level": "low",
            "country": country,
            "account_number": self._generate_account_number(country),
            "account_open_date": account_open_date.strftime("%Y-%m-%d"),
            "typical_transaction_range": {
                "min": random.randint(5000, 20000),
                "max": random.randint(100000, 500000)
            },
            "typical_countries": [country, random.choice(["US", "UK", "JP", "AU"])],
            "monthly_transaction_count": random.randint(3, 12),
            "notes": notes
        }

    def generate_medium_risk_customer(self) -> Dict:
        """
        Generate medium-risk customer profile
        生成中風險客戶檔案

        Characteristics: Offshore companies or recent accounts, partial documentation
        特徵：離岸公司或近期開戶，部分文件不完整
        """
        customer_type = random.choice(["corporate", "individual"])
        country = random.choice(["KY", "BVI", "HK", "SG", "UK"])

        if customer_type == "corporate":
            name = f"{fake.company()} {random.choice(['Holdings', 'International', 'Global', 'Ventures'])} Ltd"
            notes = f"Offshore holding company, cross-border transactions"
        else:
            name = fake.name()
            notes = f"Recent account holder, building transaction history"

        kyc_status = random.choice(["verified", "pending", "verified"])
        account_open_date = datetime.now() - timedelta(days=random.randint(90, 730))

        return {
            "customer_id": f"C-{self.customer_id_counter:05d}",
            "name": name,
            "type": customer_type,
            "kyc_status": kyc_status,
            "risk_level": "medium",
            "country": country,
            "account_number": self._generate_account_number(country),
            "account_open_date": account_open_date.strftime("%Y-%m-%d"),
            "typical_transaction_range": {
                "min": random.randint(100000, 300000),
                "max": random.randint(500000, 2000000)
            },
            "typical_countries": [country, random.choice(["HK", "SG", "US", "CN", "UK"])],
            "monthly_transaction_count": random.randint(2, 8),
            "notes": notes
        }

    def generate_high_risk_customer(self) -> Dict:
        """
        Generate high-risk customer profile
        生成高風險客戶檔案

        Characteristics: PEP or FATF high-risk jurisdictions
        特徵：政治敏感人士或涉及 FATF 高風險名單國家
        """
        customer_type = random.choice(["individual", "corporate"])
        # FATF high-risk jurisdictions (as of 2024)
        country = random.choice(["KY", "BVI", "KP", "IR", "MM"])

        if customer_type == "individual":
            name = fake.name()
            notes = f"Politically Exposed Person (PEP), requires enhanced due diligence"
        else:
            name = f"{fake.company()} {random.choice(['Corp', 'Holdings', 'Enterprises'])} Ltd"
            notes = f"High-risk jurisdiction entity, complex ownership structure"

        kyc_status = random.choice(["verified", "expired", "pending"])
        account_open_date = datetime.now() - timedelta(days=random.randint(180, 1095))

        return {
            "customer_id": f"C-{self.customer_id_counter:05d}",
            "name": name,
            "type": customer_type,
            "kyc_status": kyc_status,
            "risk_level": "high",
            "country": country,
            "account_number": self._generate_account_number(country),
            "account_open_date": account_open_date.strftime("%Y-%m-%d"),
            "typical_transaction_range": {
                "min": random.randint(200000, 500000),
                "max": random.randint(1000000, 5000000)
            },
            "typical_countries": [country, random.choice(["CN", "RU", "IR", "KP", "MM"])],
            "monthly_transaction_count": random.randint(1, 5),
            "notes": notes
        }

    def generate_all_customers(self, low_count: int = 60, medium_count: int = 30, high_count: int = 10) -> List[Dict]:
        """
        Generate all customer profiles
        生成所有客戶檔案

        Args:
            low_count: Number of low-risk customers
            medium_count: Number of medium-risk customers
            high_count: Number of high-risk customers
        """
        print(f"Generating {low_count} low-risk customers...")
        for _ in range(low_count):
            customer = self.generate_low_risk_customer()
            self.generated_customers.append(customer)
            self.customer_id_counter += 1

        print(f"Generating {medium_count} medium-risk customers...")
        for _ in range(medium_count):
            customer = self.generate_medium_risk_customer()
            self.generated_customers.append(customer)
            self.customer_id_counter += 1

        print(f"Generating {high_count} high-risk customers...")
        for _ in range(high_count):
            customer = self.generate_high_risk_customer()
            self.generated_customers.append(customer)
            self.customer_id_counter += 1

        print(f"✓ Generated {len(self.generated_customers)} total customers")
        return self.generated_customers

    def save_to_file(self, output_path: Path):
        """
        Save generated customers to JSON file
        將生成的客戶保存到 JSON 文件
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.generated_customers, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved to {output_path}")


def main():
    """Main execution function / 主執行函數"""
    print("=" * 70)
    print("  Customer Data Generator / 客戶數據生成器")
    print("=" * 70)

    generator = CustomerGenerator()
    customers = generator.generate_all_customers(low_count=60, medium_count=30, high_count=10)

    # Save to seeds directory
    output_path = Path(__file__).parent.parent / "seeds" / "customers.json"
    generator.save_to_file(output_path)

    # Print summary
    print("\n" + "=" * 70)
    print("  Summary / 摘要")
    print("=" * 70)
    print(f"  Total Customers: {len(customers)}")
    print(f"  Low Risk: {sum(1 for c in customers if c['risk_level'] == 'low')}")
    print(f"  Medium Risk: {sum(1 for c in customers if c['risk_level'] == 'medium')}")
    print(f"  High Risk: {sum(1 for c in customers if c['risk_level'] == 'high')}")
    print(f"  Individual: {sum(1 for c in customers if c['type'] == 'individual')}")
    print(f"  Corporate: {sum(1 for c in customers if c['type'] == 'corporate')}")
    print()


if __name__ == "__main__":
    main()
