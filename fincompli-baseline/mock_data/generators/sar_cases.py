"""
SAR Cases Data Generator
SAR 案件數據生成器

Generates 30 realistic historical SAR (Suspicious Activity Report) cases.
生成 30 條真實的歷史可疑活動報告案件。

Case Distribution / 案件分佈:
- Structuring (10): Breaking large amounts into smaller transactions
- Money Laundering (8): Complex layering and integration schemes
- Fraud (7): Identity theft, invoice fraud, etc.
- Terrorist Financing (3): Funding of terrorist activities
- Other (2): Unusual patterns not fitting other categories

[Business Purpose] Provides episodic memory for case history retrieval
[業務目的] 為案例歷史檢索提供情節記憶
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
import random
from typing import List, Dict
from faker import Faker

fake = Faker('en_US')
Faker.seed(43)
random.seed(43)


class SARCaseGenerator:
    """
    SAR Case Data Generator
    SAR 案件數據生成器
    """

    def __init__(self):
        self.case_id_counter = 1
        self.generated_cases: List[Dict] = []

    def generate_structuring_case(self) -> Dict:
        """
        Generate structuring case (breaking large amounts into smaller transactions)
        生成結構化分拆案件（將大額拆分為小額交易）
        """
        customer_id = f"C-{random.randint(1, 100):05d}"
        year = random.choice([2023, 2024])
        month = random.randint(1, 12)

        # Multiple transactions just below reporting threshold
        num_transactions = random.randint(3, 5)
        amount_per_txn = random.randint(480000, 499000)
        total_amount = amount_per_txn * num_transactions

        jurisdictions = random.sample(["HK", "SG", "KY", "BVI", "US", "UK"], k=random.randint(2, 4))

        case_summary = (
            f"Customer {customer_id} conducted {num_transactions} transactions within "
            f"{random.randint(30, 180)} minutes, each amount ranging HKD {amount_per_txn:,} to HKD {amount_per_txn + 10000:,}, "
            f"totaling HKD {total_amount:,}. Transactions originated from multiple jurisdictions "
            f"({', '.join(jurisdictions)}). Each transaction was deliberately structured below the "
            f"HKD 500,000 reporting threshold. Customer provided vague business explanations when questioned. "
            f"Pattern consistent with deliberate avoidance of regulatory reporting requirements."
        )

        return {
            "sar_id": f"SAR-{year}-{self.case_id_counter:04d}",
            "filed_date": f"{year}-{month:02d}-{random.randint(1, 28):02d}",
            "customer_id": customer_id,
            "case_type": "structuring",
            "transaction_pattern": f"{num_transactions} transactions just below HKD 500K threshold across {len(jurisdictions)} jurisdictions",
            "amount_total": total_amount,
            "jurisdictions_involved": jurisdictions,
            "suspicious_indicators": [
                "Multiple transactions below reporting threshold",
                "Short time window between transactions",
                "Multiple jurisdiction coordination",
                "Vague business purpose explanation",
                "Pattern of repeated behavior"
            ],
            "regulations_cited": ["HKMA AML § 35", "FSTB Notice 2024-01", "FinCEN § 103.18"],
            "outcome": random.choice(["filed", "referred_to_police"]),
            "case_summary": case_summary,
            "lessons_learned": "Structuring detection requires monitoring transaction patterns across jurisdictions within short time windows. Key indicator: amounts consistently just below thresholds."
        }

    def generate_money_laundering_case(self) -> Dict:
        """
        Generate money laundering case
        生成洗錢案件
        """
        customer_id = f"C-{random.randint(1, 100):05d}"
        year = random.choice([2022, 2023, 2024])
        month = random.randint(1, 12)

        total_amount = random.randint(2000000, 8000000)
        jurisdictions = random.sample(["HK", "SG", "KY", "BVI", "CH", "LU", "UAE"], k=random.randint(3, 5))

        layering_methods = random.sample([
            "shell company transfers",
            "cryptocurrency conversion",
            "real estate transactions",
            "trade-based schemes",
            "loan-back arrangements"
        ], k=random.randint(2, 3))

        case_summary = (
            f"Complex money laundering scheme involving customer {customer_id} with total funds "
            f"movement of approximately HKD {total_amount:,}. The scheme involved {len(jurisdictions)} "
            f"jurisdictions ({', '.join(jurisdictions)}) and utilized {', '.join(layering_methods)} "
            f"to obscure the origin of funds. Initial funds appeared to originate from {random.choice(['unverified overseas sources', 'high-risk jurisdictions', 'shell company network'])}. "
            f"Investigation revealed {random.randint(5, 12)} interconnected offshore entities with "
            f"unclear beneficial ownership. Customer unable to provide legitimate source of wealth documentation."
        )

        return {
            "sar_id": f"SAR-{year}-{self.case_id_counter:04d}",
            "filed_date": f"{year}-{month:02d}-{random.randint(1, 28):02d}",
            "customer_id": customer_id,
            "case_type": "money_laundering",
            "transaction_pattern": f"Complex layering through {len(jurisdictions)} jurisdictions using {', '.join(layering_methods)}",
            "amount_total": total_amount,
            "jurisdictions_involved": jurisdictions,
            "suspicious_indicators": [
                "Unclear source of funds",
                "Complex offshore structure",
                "Rapid movement through multiple jurisdictions",
                "Use of intermediary entities",
                "Inconsistent business activities"
            ],
            "regulations_cited": ["HKMA AML § 35", "FATF Recommendation 10", "MAS Notice 626"],
            "outcome": random.choice(["referred_to_police", "filed"]),
            "case_summary": case_summary,
            "lessons_learned": "Money laundering schemes often involve multiple jurisdictions and complex entity structures. Enhanced due diligence on beneficial ownership is critical."
        }

    def generate_fraud_case(self) -> Dict:
        """
        Generate fraud case
        生成詐欺案件
        """
        customer_id = f"C-{random.randint(1, 100):05d}"
        year = random.choice([2023, 2024])
        month = random.randint(1, 12)

        fraud_types = [
            ("invoice fraud", "falsified commercial invoices"),
            ("identity theft", "stolen identity credentials"),
            ("phishing scheme", "phishing emails targeting corporate accounts"),
            ("advance fee fraud", "advance payment fraud scheme"),
            ("trade-based fraud", "over-invoicing of goods")
        ]

        fraud_type, description = random.choice(fraud_types)
        total_amount = random.randint(500000, 3000000)

        case_summary = (
            f"Fraud investigation of customer {customer_id} revealed {description}. "
            f"Total fraudulent amount: HKD {total_amount:,}. The scheme involved "
            f"{random.randint(3, 8)} victim companies in {random.choice(['HK', 'SG', 'CN'])} and "
            f"{random.choice(['UK', 'US', 'AU'])}. Investigation showed {random.choice(['forged documents', 'manipulated invoices', 'false representations'])} "
            f"used to deceive counterparties. Funds were quickly moved to {random.choice(['offshore accounts', 'cryptocurrency exchanges', 'unrelated third parties'])} "
            f"upon receipt. Multiple complaints received from affected parties."
        )

        return {
            "sar_id": f"SAR-{year}-{self.case_id_counter:04d}",
            "filed_date": f"{year}-{month:02d}-{random.randint(1, 28):02d}",
            "customer_id": customer_id,
            "case_type": "fraud",
            "transaction_pattern": f"{fraud_type} targeting {random.randint(3, 8)} victims",
            "amount_total": total_amount,
            "jurisdictions_involved": random.sample(["HK", "SG", "CN", "UK", "US", "AU"], k=random.randint(2, 3)),
            "suspicious_indicators": [
                "Forged or manipulated documents",
                "Multiple victim complaints",
                "Rapid fund movement post-receipt",
                "Inconsistent business explanations",
                "Use of intermediary accounts"
            ],
            "regulations_cited": ["HKMA AML § 35", "Fraud Ordinance Cap 210"],
            "outcome": random.choice(["referred_to_police", "filed"]),
            "case_summary": case_summary,
            "lessons_learned": f"Fraud detection requires verification of supporting documents and monitoring for rapid fund movements after receipt. {fraud_type.capitalize()} patterns should trigger enhanced scrutiny."
        }

    def generate_terrorist_financing_case(self) -> Dict:
        """
        Generate terrorist financing case
        生成恐怖融資案件
        """
        customer_id = f"C-{random.randint(1, 100):05d}"
        year = random.choice([2023, 2024])
        month = random.randint(1, 12)

        total_amount = random.randint(50000, 500000)  # Usually smaller amounts
        high_risk_jurisdictions = random.sample(["IR", "SY", "YE", "AF", "PK"], k=random.randint(1, 3))

        case_summary = (
            f"Suspicious transaction pattern from customer {customer_id} involving transfers "
            f"totaling HKD {total_amount:,} to high-risk jurisdictions ({', '.join(high_risk_jurisdictions)}). "
            f"Transactions were structured as {random.choice(['charitable donations', 'personal remittances', 'business payments'])} "
            f"but recipient entities could not be verified. Customer has known associations with "
            f"{random.choice(['individuals on sanctions lists', 'entities in conflict zones', 'unregistered NPOs'])}. "
            f"Pattern of regular small transfers to same destinations over {random.randint(3, 12)} month period. "
            f"Enhanced due diligence revealed inconsistencies in stated purpose and actual use of funds."
        )

        return {
            "sar_id": f"SAR-{year}-{self.case_id_counter:04d}",
            "filed_date": f"{year}-{month:02d}-{random.randint(1, 28):02d}",
            "customer_id": customer_id,
            "case_type": "terrorist_financing",
            "transaction_pattern": f"Regular small transfers to high-risk jurisdictions over extended period",
            "amount_total": total_amount,
            "jurisdictions_involved": ["HK"] + high_risk_jurisdictions,
            "suspicious_indicators": [
                "Transfers to high-risk jurisdictions",
                "Recipient verification failed",
                "Known associations with sanctioned entities",
                "Inconsistent stated purpose",
                "Pattern of regular transfers"
            ],
            "regulations_cited": [
                "UNSCR 1373 (Counter-Terrorism)",
                "HKMA AML § 35",
                "FATF Recommendation 5"
            ],
            "outcome": "referred_to_police",
            "case_summary": case_summary,
            "lessons_learned": "Terrorist financing often involves smaller amounts but to high-risk jurisdictions. Key red flag: inability to verify recipient entities combined with customer links to sanctioned persons or entities."
        }

    def generate_other_case(self) -> Dict:
        """
        Generate other suspicious activity case
        生成其他可疑活動案件
        """
        customer_id = f"C-{random.randint(1, 100):05d}"
        year = random.choice([2023, 2024])
        month = random.randint(1, 12)

        total_amount = random.randint(800000, 2500000)

        case_summary = (
            f"Unusual transaction pattern from customer {customer_id} that did not fit typical "
            f"typologies but raised suspicion. Total amount: HKD {total_amount:,}. Activity involved "
            f"{random.choice(['sudden change in transaction behavior', 'unexplained wealth increase', 'inconsistent with business profile'])}. "
            f"Customer provided {random.choice(['conflicting explanations', 'incomplete documentation', 'evasive responses'])} "
            f"when questioned. Enhanced monitoring revealed {random.choice(['related-party transactions with no commercial rationale', 'circular fund flows', 'transactions inconsistent with stated income'])}. "
            f"While not clearly fitting standard typologies, the overall pattern warranted reporting for further investigation."
        )

        return {
            "sar_id": f"SAR-{year}-{self.case_id_counter:04d}",
            "filed_date": f"{year}-{month:02d}-{random.randint(1, 28):02d}",
            "customer_id": customer_id,
            "case_type": "other",
            "transaction_pattern": "Unusual behavior not fitting standard typologies",
            "amount_total": total_amount,
            "jurisdictions_involved": random.sample(["HK", "SG", "CN", "US", "UK"], k=random.randint(2, 3)),
            "suspicious_indicators": [
                "Deviation from expected behavior",
                "Inadequate explanation",
                "Inconsistent with customer profile",
                "Red flags without clear typology"
            ],
            "regulations_cited": ["HKMA AML § 35"],
            "outcome": random.choice(["filed", "dismissed"]),
            "case_summary": case_summary,
            "lessons_learned": "Not all suspicious activity fits neat categories. File SAR when pattern raises legitimate concerns even without clear typology match."
        }

    def generate_all_cases(self) -> List[Dict]:
        """
        Generate all SAR cases according to distribution
        按分佈生成所有 SAR 案件
        """
        print("Generating 10 structuring cases...")
        for _ in range(10):
            case = self.generate_structuring_case()
            self.generated_cases.append(case)
            self.case_id_counter += 1

        print("Generating 8 money laundering cases...")
        for _ in range(8):
            case = self.generate_money_laundering_case()
            self.generated_cases.append(case)
            self.case_id_counter += 1

        print("Generating 7 fraud cases...")
        for _ in range(7):
            case = self.generate_fraud_case()
            self.generated_cases.append(case)
            self.case_id_counter += 1

        print("Generating 3 terrorist financing cases...")
        for _ in range(3):
            case = self.generate_terrorist_financing_case()
            self.generated_cases.append(case)
            self.case_id_counter += 1

        print("Generating 2 other cases...")
        for _ in range(2):
            case = self.generate_other_case()
            self.generated_cases.append(case)
            self.case_id_counter += 1

        print(f"✓ Generated {len(self.generated_cases)} total SAR cases")
        return self.generated_cases

    def save_to_file(self, output_path: Path):
        """Save generated cases to JSON file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.generated_cases, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved to {output_path}")


def main():
    """Main execution function"""
    print("=" * 70)
    print("  SAR Cases Data Generator / SAR 案件數據生成器")
    print("=" * 70)

    generator = SARCaseGenerator()
    cases = generator.generate_all_cases()

    # Save to seeds directory
    output_path = Path(__file__).parent.parent / "seeds" / "sar_cases.json"
    generator.save_to_file(output_path)

    # Print summary
    print("\n" + "=" * 70)
    print("  Summary / 摘要")
    print("=" * 70)
    print(f"  Total Cases: {len(cases)}")
    print(f"  Structuring: {sum(1 for c in cases if c['case_type'] == 'structuring')}")
    print(f"  Money Laundering: {sum(1 for c in cases if c['case_type'] == 'money_laundering')}")
    print(f"  Fraud: {sum(1 for c in cases if c['case_type'] == 'fraud')}")
    print(f"  Terrorist Financing: {sum(1 for c in cases if c['case_type'] == 'terrorist_financing')}")
    print(f"  Other: {sum(1 for c in cases if c['case_type'] == 'other')}")
    print()


if __name__ == "__main__":
    main()
