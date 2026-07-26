"""
Transaction Scenarios Generator

Generates 25 realistic transaction test scenarios across 5 categories.

Scenario Types:
1. Normal Cross-Border Transfer (5) - Low risk baseline
2. Structuring (5) - High risk, primary demo scenario
3. Geographic Anomaly (5) - Medium risk, unusual destinations
4. Expired KYC High-Value (5) - Medium risk, documentation issues
5. False Positive (5) - Appears suspicious but legitimate

[Business Purpose] Provides realistic test cases for compliance analysis
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
import random
from typing import List, Dict
from faker import Faker

fake = Faker('en_US')
Faker.seed(44)
random.seed(44)


class TransactionScenarioGenerator:
    """
    Transaction Scenario Generator
    """

    def __init__(self):
        self.transaction_id_counter = 1
        self.generated_scenarios: List[Dict] = []

    def _generate_transaction_id(self, date: datetime) -> str:
        """Generate transaction ID with date prefix"""
        return f"TXN-{date.strftime('%Y%m%d')}-{self.transaction_id_counter:05d}"

    def generate_normal_transfers(self) -> List[Dict]:
        """
        Scenario 1: Normal Cross-Border Transfers

        Characteristics: Clear business purpose, within customer profile, proper documentation
        """
        scenarios = []

        for i in range(5):
            timestamp = datetime.now() - timedelta(days=random.randint(1, 30))
            customer_id = f"C-{random.randint(1, 60):05d}"  # Low-risk customers

            transaction = {
                "transaction_id": self._generate_transaction_id(timestamp),
                "timestamp": timestamp.isoformat(),
                "customer_id": customer_id,
                "customer_name": fake.company() + " Ltd",
                "from_account": f"HK{random.randint(10,99)} {random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}",
                "to_account": f"SG{random.randint(10,99)} DBS{random.randint(1000,9999)} {random.randint(10000,99999)}",
                "to_country": "SG",
                "to_beneficiary": fake.company() + " Pte Ltd",
                "amount": random.randint(100000, 300000),
                "currency": "HKD",
                "purpose_code": "TRADE",
                "purpose_description": "Payment for imported goods - Invoice #" + str(random.randint(10000, 99999)),
                "channel": "swift",
                "supporting_documents": ["Commercial Invoice", "Bill of Lading", "Purchase Order"],
                "ip_address": None,
                "device_fingerprint": None,
                "scenario_type": "normal",
                "expected_risk_score": round(random.uniform(0.05, 0.15), 2),
                "expected_outcome": "clear",
                "test_notes": "Legitimate trade payment with complete documentation"
            }
            scenarios.append(transaction)
            self.transaction_id_counter += 1

        return scenarios

    def generate_structuring_scenarios(self) -> List[Dict]:
        """
        Scenario 2: Structuring (Breaking Large Amounts)

        Characteristics: Multiple transactions just below threshold, short time window, multi-jurisdiction
        """
        scenarios = []

        # Primary demo scenario - most detailed
        base_timestamp = datetime.now() - timedelta(days=5)

        # Scenario 2.1: Classic structuring - 3 transactions in 3 minutes
        main_scenario = {
            "transaction_id": self._generate_transaction_id(base_timestamp),
            "timestamp": base_timestamp.isoformat(),
            "customer_id": "C-00412",
            "customer_name": "Sunrise Global Holdings Ltd",
            "scenario_type": "structuring",
            "expected_risk_score": 0.93,
            "expected_outcome": "human_review",
            "test_notes": "PRIMARY DEMO SCENARIO - Classic structuring pattern across 3 jurisdictions",
            "related_transactions": [
                {
                    "sub_id": "TXN-88411-A",
                    "timestamp": base_timestamp.isoformat(),
                    "from_account": "HK82 0012 3456 7890",
                    "to_account": "KY1-9999-0001",
                    "to_country": "KY",
                    "to_beneficiary": "Cayman Offshore Services Inc",
                    "amount": 490000,
                    "currency": "HKD",
                    "purpose_code": "INVEST",
                    "purpose_description": "Investment transfer",
                    "channel": "swift"
                },
                {
                    "sub_id": "TXN-88411-B",
                    "timestamp": (base_timestamp + timedelta(minutes=1, seconds=30)).isoformat(),
                    "from_account": "SG29 DBS9 0000 0001",
                    "to_account": "KY1-9999-0002",
                    "to_country": "KY",
                    "to_beneficiary": "Cayman Investment Trust",
                    "amount": 490000,
                    "currency": "HKD",
                    "purpose_code": "INVEST",
                    "purpose_description": "Portfolio rebalancing",
                    "channel": "swift"
                },
                {
                    "sub_id": "TXN-88411-C",
                    "timestamp": (base_timestamp + timedelta(minutes=3)).isoformat(),
                    "from_account": "KY2-8888-0001",
                    "to_account": "BVI-0000-7777",
                    "to_country": "VG",
                    "to_beneficiary": "BVI Holdings Corp",
                    "amount": 490000,
                    "currency": "HKD",
                    "purpose_code": "INVEST",
                    "purpose_description": "Capital transfer",
                    "channel": "swift"
                }
            ]
        }
        scenarios.append(main_scenario)
        self.transaction_id_counter += 1

        # Generate 4 more structuring scenarios with variations
        for i in range(4):
            timestamp = datetime.now() - timedelta(days=random.randint(10, 60))
            num_splits = random.randint(3, 5)
            amount_per = random.randint(485000, 499000)

            related = []
            for j in range(num_splits):
                related.append({
                    "sub_id": f"TXN-{timestamp.strftime('%m%d')}{i:02d}-{chr(65+j)}",
                    "timestamp": (timestamp + timedelta(minutes=j*10)).isoformat(),
                    "from_account": f"HK{random.randint(10,99)} {random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}",
                    "to_account": f"KY{random.randint(1,9)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}",
                    "to_country": random.choice(["KY", "BVI", "VG"]),
                    "to_beneficiary": fake.company() + " " + random.choice(["Holdings", "Corp", "Ltd"]),
                    "amount": amount_per,
                    "currency": "HKD",
                    "purpose_code": random.choice(["INVEST", "LOAN", "SUPP"]),
                    "purpose_description": random.choice(["Investment", "Loan repayment", "Business payment"]),
                    "channel": "swift"
                })

            scenario = {
                "transaction_id": self._generate_transaction_id(timestamp),
                "timestamp": timestamp.isoformat(),
                "customer_id": f"C-{random.randint(61, 90):05d}",
                "customer_name": fake.company() + " International Ltd",
                "scenario_type": "structuring",
                "expected_risk_score": round(random.uniform(0.85, 0.95), 2),
                "expected_outcome": "human_review",
                "test_notes": f"Structuring: {num_splits} transactions of ~HKD {amount_per:,} each",
                "related_transactions": related
            }
            scenarios.append(scenario)
            self.transaction_id_counter += 1

        return scenarios

    def generate_geo_anomaly_scenarios(self) -> List[Dict]:
        """
        Scenario 3: Geographic Anomaly

        Characteristics: Destination country inconsistent with customer history, high-risk jurisdictions
        """
        scenarios = []
        high_risk_countries = ["IR", "KP", "MM", "AF", "SY"]

        for i in range(5):
            timestamp = datetime.now() - timedelta(days=random.randint(1, 45))
            customer_id = f"C-{random.randint(1, 60):05d}"  # Normally low-risk customer

            transaction = {
                "transaction_id": self._generate_transaction_id(timestamp),
                "timestamp": timestamp.isoformat(),
                "customer_id": customer_id,
                "customer_name": fake.name() if i % 2 == 0 else fake.company() + " Ltd",
                "from_account": f"HK{random.randint(10,99)} {random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}",
                "to_account": f"{random.choice(high_risk_countries)}-{random.randint(100000, 999999)}",
                "to_country": random.choice(high_risk_countries),
                "to_beneficiary": fake.company() + " Trading Co",
                "amount": random.randint(200000, 800000),
                "currency": "USD",
                "purpose_code": "TRADE",
                "purpose_description": random.choice([
                    "Payment for goods",
                    "Business transaction",
                    "Import payment",
                    "Service fee"
                ]),
                "channel": "swift",
                "supporting_documents": ["Invoice"],
                "ip_address": None,
                "device_fingerprint": None,
                "scenario_type": "geo_anomaly",
                "expected_risk_score": round(random.uniform(0.60, 0.75), 2),
                "expected_outcome": "human_review",
                "test_notes": f"First transaction to {random.choice(high_risk_countries)} - high-risk jurisdiction, deviates from typical pattern (HK, SG, US, UK)"
            }
            scenarios.append(transaction)
            self.transaction_id_counter += 1

        return scenarios

    def generate_kyc_expired_scenarios(self) -> List[Dict]:
        """
        Scenario 4: KYC Expired with High-Value Transaction

        Characteristics: Customer KYC documentation expired, large transaction amount
        """
        scenarios = []

        for i in range(5):
            timestamp = datetime.now() - timedelta(days=random.randint(1, 20))
            customer_id = f"C-{random.randint(61, 100):05d}"  # Medium to high risk

            transaction = {
                "transaction_id": self._generate_transaction_id(timestamp),
                "timestamp": timestamp.isoformat(),
                "customer_id": customer_id,
                "customer_name": fake.company() + " " + random.choice(["Holdings", "Ventures", "International"]),
                "from_account": f"HK{random.randint(10,99)} {random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}",
                "to_account": f"UK{random.randint(10,99)} {random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}",
                "to_country": random.choice(["UK", "US", "CH", "LU"]),
                "to_beneficiary": fake.company() + " PLC",
                "amount": random.randint(800000, 2000000),
                "currency": "USD",
                "purpose_code": "INVEST",
                "purpose_description": "Investment portfolio transfer",
                "channel": "swift",
                "supporting_documents": ["Transfer Request"],
                "ip_address": None,
                "device_fingerprint": None,
                "kyc_status": "expired",
                "kyc_expiry_date": (datetime.now() - timedelta(days=random.randint(30, 180))).strftime("%Y-%m-%d"),
                "scenario_type": "kyc_expired",
                "expected_risk_score": round(random.uniform(0.55, 0.70), 2),
                "expected_outcome": "human_review",
                "test_notes": "High-value transaction with expired KYC - requires immediate KYC refresh and enhanced review"
            }
            scenarios.append(transaction)
            self.transaction_id_counter += 1

        return scenarios

    def generate_false_positive_scenarios(self) -> List[Dict]:
        """
        Scenario 5: False Positive

        Characteristics: Appears suspicious initially but has legitimate business explanation
        """
        scenarios = []

        for i in range(5):
            timestamp = datetime.now() - timedelta(days=random.randint(1, 15))
            customer_id = f"C-{random.randint(1, 60):05d}"  # Low-risk customer

            # Legitimate reasons for unusual patterns
            legitimate_reasons = [
                {
                    "reason": "Quarter-end subsidiary funding",
                    "docs": ["Board Resolution", "Internal Transfer Authorization", "Audited Financial Statements"],
                    "note": "Publicly-listed company transferring funds to 5 overseas subsidiaries for quarter-end financial planning"
                },
                {
                    "reason": "Annual bonus distribution to overseas employees",
                    "docs": ["Employment Contracts", "Bonus Approval Letter", "Payroll Records"],
                    "note": "Regular annual bonus payment to international staff across multiple countries"
                },
                {
                    "reason": "Large equipment purchase with installment payments",
                    "docs": ["Purchase Agreement", "Equipment Invoice", "Payment Schedule"],
                    "note": "Scheduled installment payment for industrial equipment purchase, amounts appear large but are contractual"
                },
                {
                    "reason": "Insurance claim settlement distribution",
                    "docs": ["Insurance Policy", "Claim Settlement Letter", "Distribution Schedule"],
                    "note": "Insurance company distributing claim settlements to multiple claimants"
                },
                {
                    "reason": "Property sale proceeds distribution to co-owners",
                    "docs": ["Property Sale Agreement", "Title Deed", "Co-ownership Agreement"],
                    "note": "Property sale proceeds being distributed to multiple co-owners as per legal agreement"
                }
            ]

            reason_data = random.choice(legitimate_reasons)

            transaction = {
                "transaction_id": self._generate_transaction_id(timestamp),
                "timestamp": timestamp.isoformat(),
                "customer_id": customer_id,
                "customer_name": fake.company() + " " + random.choice(["Ltd", "PLC", "Corporation"]),
                "from_account": f"HK{random.randint(10,99)} {random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}",
                "to_account": f"UK{random.randint(10,99)} {random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}",
                "to_country": random.choice(["UK", "US", "AU", "JP", "SG"]),
                "to_beneficiary": fake.company() + " Inc",
                "amount": random.randint(500000, 1500000),
                "currency": "HKD",
                "purpose_code": "SUPP",
                "purpose_description": reason_data["reason"],
                "channel": "swift",
                "supporting_documents": reason_data["docs"],
                "legitimate_explanation": reason_data["reason"],
                "ip_address": None,
                "device_fingerprint": None,
                "scenario_type": "false_positive",
                "expected_risk_score": round(random.uniform(0.40, 0.60), 2),
                "expected_outcome": "clear",
                "test_notes": reason_data["note"]
            }
            scenarios.append(transaction)
            self.transaction_id_counter += 1

        return scenarios

    def generate_all_scenarios(self) -> List[Dict]:
        """
        Generate all transaction scenarios
        """
        print("Generating 5 normal transfer scenarios...")
        self.generated_scenarios.extend(self.generate_normal_transfers())

        print("Generating 5 structuring scenarios (including PRIMARY DEMO)...")
        self.generated_scenarios.extend(self.generate_structuring_scenarios())

        print("Generating 5 geographic anomaly scenarios...")
        self.generated_scenarios.extend(self.generate_geo_anomaly_scenarios())

        print("Generating 5 KYC expired scenarios...")
        self.generated_scenarios.extend(self.generate_kyc_expired_scenarios())

        print("Generating 5 false positive scenarios...")
        self.generated_scenarios.extend(self.generate_false_positive_scenarios())

        print(f"✓ Generated {len(self.generated_scenarios)} total transaction scenarios")
        return self.generated_scenarios

    def save_to_file(self, output_path: Path):
        """Save generated scenarios to JSON file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.generated_scenarios, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved to {output_path}")


def main():
    """Main execution function"""
    print("=" * 70)
    print("  Transaction Scenarios Generator")
    print("=" * 70)

    generator = TransactionScenarioGenerator()
    scenarios = generator.generate_all_scenarios()

    # Save to seeds directory
    output_path = Path(__file__).parent.parent / "seeds" / "transaction_scenarios.json"
    generator.save_to_file(output_path)

    # Print summary
    print("\n" + "=" * 70)
    print("  Summary")
    print("=" * 70)
    print(f"  Total Scenarios: {len(scenarios)}")
    print(f"  Normal: {sum(1 for s in scenarios if s['scenario_type'] == 'normal')}")
    print(f"  Structuring: {sum(1 for s in scenarios if s['scenario_type'] == 'structuring')}")
    print(f"  Geographic Anomaly: {sum(1 for s in scenarios if s['scenario_type'] == 'geo_anomaly')}")
    print(f"  KYC Expired: {sum(1 for s in scenarios if s['scenario_type'] == 'kyc_expired')}")
    print(f"  False Positive: {sum(1 for s in scenarios if s['scenario_type'] == 'false_positive')}")
    print()
    print("  ⭐ PRIMARY DEMO: Scenario with customer_id='C-00412' (Structuring)")
    print()


if __name__ == "__main__":
    main()
