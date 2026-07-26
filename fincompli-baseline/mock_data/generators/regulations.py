"""
Regulatory Text Generator

Generates 40 realistic regulatory text segments from major AML/compliance frameworks.
Generates 40 realistic regulatory text segments from major AML/compliance frameworks.

Distribution:
- HKMA Anti-Money Laundering Guideline 2023: 15 sections
- MAS Notice 626 (Singapore): 10 sections
- FinCEN BSA/AML Requirements: 10 sections
- FATF 40 Recommendations: 5 sections

[Business Purpose] Provides semantic memory for compliance research
"""

import json
from pathlib import Path
from typing import List, Dict

class RegulationGenerator:
    """
    Regulatory Text Generator
    """

    def __init__(self):
        self.generated_regulations: List[Dict] = []

    def generate_hkma_regulations(self) -> List[Dict]:
        """
        Generate HKMA AML Guidelines
        """
        regulations = [
            {
                "regulation_id": "HKMA-AML-2023-§35",
                "jurisdiction": "HK",
                "authority": "HKMA",
                "section": "§ 35",
                "title": "Suspicious Transaction Reporting Obligation",
                "content": "An authorized institution must file a Suspicious Transaction Report (STR) with the Joint Financial Intelligence Unit (JFIU) where it knows or suspects that any property represents the proceeds of an indictable offence, or is intended to be used for terrorist financing. The report must be made as soon as reasonably practicable after forming the knowledge or suspicion.",
                "applicability": "Applies when institution knows or suspects proceeds of crime or terrorist financing",
                "deadline": "As soon as reasonably practicable, typically within 3 business days",
                "penalty": "Up to HKD 1,000,000 and imprisonment for 2 years"
            },
            {
                "regulation_id": "HKMA-AML-2023-§12",
                "jurisdiction": "HK",
                "authority": "HKMA",
                "section": "§ 12",
                "title": "Customer Due Diligence Requirements",
                "content": "Authorized institutions must conduct customer due diligence (CDD) when establishing business relations, carrying out occasional transactions above HKD 120,000, or when there is suspicion of money laundering or terrorist financing. CDD includes verifying customer identity using reliable, independent source documents, data or information.",
                "applicability": "Required for all new customer relationships and high-value transactions",
                "deadline": "Before establishing business relationship or conducting transaction",
                "penalty": "Regulatory sanctions including license restrictions"
            },
            {
                "regulation_id": "HKMA-AML-2023-§18",
                "jurisdiction": "HK",
                "authority": "HKMA",
                "section": "§ 18",
                "title": "Enhanced Due Diligence for High-Risk Customers",
                "content": "Enhanced due diligence (EDD) measures must be applied to customers and transactions presenting higher risks of money laundering or terrorist financing. This includes politically exposed persons (PEPs), customers from high-risk jurisdictions, and complex corporate structures. EDD requires additional information on source of funds and wealth, increased monitoring frequency, and senior management approval.",
                "applicability": "Mandatory for PEPs, high-risk jurisdictions, and other elevated risk scenarios",
                "deadline": "Before establishing relationship or as risk assessment changes",
                "penalty": "Regulatory enforcement actions"
            },
            {
                "regulation_id": "HKMA-AML-2023-§42",
                "jurisdiction": "HK",
                "authority": "HKMA",
                "section": "§ 42",
                "title": "Record Keeping Requirements",
                "content": "Authorized institutions must maintain records of all transactions, both domestic and international, for at least 5 years after completion. Records must be sufficient to permit reconstruction of individual transactions including customer identity documents, account files, business correspondence, and transaction records.",
                "applicability": "All customer relationships and transactions",
                "deadline": "5 years retention period from transaction date or relationship termination",
                "penalty": "Administrative penalties up to HKD 10,000,000"
            },
            {
                "regulation_id": "HKMA-AML-2023-§28",
                "jurisdiction": "HK",
                "authority": "HKMA",
                "section": "§ 28",
                "title": "Ongoing Monitoring of Business Relationships",
                "content": "Authorized institutions must conduct ongoing monitoring of business relationships to ensure transactions are consistent with their knowledge of the customer, business and risk profile. This includes scrutiny of transactions throughout the relationship to ensure consistency with customer profile and detecting unusual or suspicious patterns.",
                "applicability": "All existing customer relationships on continuous basis",
                "deadline": "Ongoing throughout relationship",
                "penalty": "Regulatory sanctions"
            },
            {
                "regulation_id": "HKMA-AML-2023-§45",
                "jurisdiction": "HK",
                "authority": "HKMA",
                "section": "§ 45",
                "title": "Tipping Off Prohibition",
                "content": "No person may disclose to a customer or third party that an STR has been or will be filed, or that a money laundering or terrorist financing investigation is being or may be conducted. Violations of the tipping off prohibition may alert criminals and jeopardize investigations.",
                "applicability": "All staff with knowledge of STR filing",
                "deadline": "Prohibition applies indefinitely",
                "penalty": "Imprisonment for 3 months and fine of HKD 50,000"
            },
            {
                "regulation_id": "HKMA-AML-2023-§8",
                "jurisdiction": "HK",
                "authority": "HKMA",
                "section": "§ 8",
                "title": "Risk Assessment and Risk-Based Approach",
                "content": "Authorized institutions must identify, assess and understand their money laundering and terrorist financing risks in relation to customers, countries, products, services and transactions. Risk assessments must be documented and kept up-to-date. A risk-based approach means applying enhanced measures for higher risks and simplified measures where risks are lower.",
                "applicability": "Enterprise-wide risk assessment required",
                "deadline": "Initial assessment before operations, reviewed at least annually",
                "penalty": "Regulatory enforcement actions"
            },
            {
                "regulation_id": "HKMA-AML-2023-§51",
                "jurisdiction": "HK",
                "authority": "HKMA",
                "section": "§ 51",
                "title": "Wire Transfer Requirements",
                "content": "For cross-border wire transfers of HKD 8,000 or more, complete originator information must accompany the transfer through the payment chain. This includes name, account number, and address. Beneficiary institutions must detect missing information and take appropriate action.",
                "applicability": "All cross-border wire transfers above threshold",
                "deadline": "Information must accompany each transfer",
                "penalty": "Financial penalties"
            },
            {
                "regulation_id": "HKMA-AML-2023-§33",
                "jurisdiction": "HK",
                "authority": "HKMA",
                "section": "§ 33",
                "title": "Politically Exposed Persons (PEPs)",
                "content": "Authorized institutions must have appropriate risk management systems to determine whether a customer or beneficial owner is a PEP. Enhanced due diligence measures for PEPs include obtaining senior management approval, establishing source of wealth and funds, and conducting enhanced ongoing monitoring.",
                "applicability": "All customers assessed for PEP status",
                "deadline": "At onboarding and periodically thereafter",
                "penalty": "Regulatory sanctions"
            },
            {
                "regulation_id": "HKMA-AML-2023-§63",
                "jurisdiction": "HK",
                "authority": "HKMA",
                "section": "§ 63",
                "title": "Staff Training Requirements",
                "content": "Authorized institutions must provide regular AML/CFT training to relevant staff. Training must cover legal requirements, internal policies, customer due diligence procedures, suspicious transaction identification, and reporting obligations. Training effectiveness must be assessed.",
                "applicability": "All staff handling customer relationships or transactions",
                "deadline": "At hiring and at least annually thereafter",
                "penalty": "Regulatory sanctions for inadequate training programs"
            },
            {
                "regulation_id": "HKMA-AML-2023-§38",
                "jurisdiction": "HK",
                "authority": "HKMA",
                "section": "§ 38",
                "title": "Correspondent Banking Due Diligence",
                "content": "Before establishing correspondent banking relationships, institutions must gather sufficient information about respondent institutions, assess ML/TF risks, obtain senior management approval, document AML/CFT responsibilities, and ensure the respondent has conducted CDD on customers with direct access to accounts.",
                "applicability": "All correspondent banking relationships",
                "deadline": "Before establishing relationship",
                "penalty": "Regulatory enforcement"
            },
            {
                "regulation_id": "HKMA-AML-2023-§71",
                "jurisdiction": "HK",
                "authority": "HKMA",
                "section": "§ 71",
                "title": "Beneficial Ownership Identification",
                "content": "Institutions must identify the beneficial owner and take reasonable measures to verify identity. Beneficial owner means the natural person who ultimately owns or controls the customer or on whose behalf a transaction is conducted. For corporate customers, this includes persons holding 10% or more ownership interest.",
                "applicability": "All corporate and legal arrangement customers",
                "deadline": "At relationship establishment",
                "penalty": "Regulatory penalties"
            },
            {
                "regulation_id": "HKMA-AML-2023-§55",
                "jurisdiction": "HK",
                "authority": "HKMA",
                "section": "§ 55",
                "title": "New Technologies and Products Risk Assessment",
                "content": "Prior to launching new products, services, or technologies, institutions must assess ML/TF risks and implement appropriate mitigation measures. This includes new delivery mechanisms, use of new or developing technologies, and use of virtual assets.",
                "applicability": "All new products, services and delivery channels",
                "deadline": "Before launch",
                "penalty": "Product approval may be revoked"
            },
            {
                "regulation_id": "HKMA-AML-2023-§48",
                "jurisdiction": "HK",
                "authority": "HKMA",
                "section": "§ 48",
                "title": "Targeted Financial Sanctions",
                "content": "Institutions must screen customers and transactions against designated lists for terrorism financing and proliferation financing sanctions. This includes UN Security Council sanctions lists and local designation lists. Matches must be reported immediately to relevant authorities.",
                "applicability": "All customers and transactions",
                "deadline": "Screening before transaction execution",
                "penalty": "Criminal prosecution for sanctions violations"
            },
            {
                "regulation_id": "HKMA-AML-2023-§58",
                "jurisdiction": "HK",
                "authority": "HKMA",
                "section": "§ 58",
                "title": "Group-Wide AML/CFT Programs",
                "content": "Financial groups must implement group-wide AML/CFT programs covering all branches and majority-owned subsidiaries. Programs must include policies, procedures, information sharing, compliance function, audit, and training. Foreign branches must apply host country requirements where more stringent.",
                "applicability": "Financial groups with international operations",
                "deadline": "Ongoing",
                "penalty": "Consolidated supervision enforcement"
            }
        ]
        return regulations

    def generate_mas_regulations(self) -> List[Dict]:
        """
        Generate MAS Notice 626 (Singapore)
        """
        regulations = [
            {
                "regulation_id": "MAS-626-§6.1",
                "jurisdiction": "SG",
                "authority": "MAS",
                "section": "§ 6.1",
                "title": "Customer Due Diligence Measures",
                "content": "A financial institution shall perform customer due diligence measures when establishing business relations, carrying out any transaction of SGD 20,000 or more, carrying out any funds transfer of SGD 1,500 or more, or when there is suspicion of money laundering or terrorism financing.",
                "applicability": "All customer onboarding and specified transactions",
                "deadline": "At specified trigger events",
                "penalty": "Financial penalties up to SGD 1,000,000"
            },
            {
                "regulation_id": "MAS-626-§11.1",
                "jurisdiction": "SG",
                "authority": "MAS",
                "section": "§ 11.1",
                "title": "Enhanced CDD for Higher Risk Categories",
                "content": "Financial institutions shall perform enhanced CDD for business relations or transactions that present higher money laundering or terrorism financing risks. This includes PEPs, correspondent relationships, and non-face-to-face business relations. Enhanced measures must be commensurate with the level of risk.",
                "applicability": "High-risk scenarios as identified",
                "deadline": "At relationship establishment or when risk increases",
                "penalty": "Regulatory enforcement actions"
            },
            {
                "regulation_id": "MAS-626-§15.1",
                "jurisdiction": "SG",
                "authority": "MAS",
                "section": "§ 15.1",
                "title": "Suspicious Transaction Reporting",
                "content": "A financial institution that knows or has reasonable grounds to suspect any property represents proceeds of drug dealing or criminal conduct, or is terrorist property, shall file a Suspicious Transaction Report (STR) with the Suspicious Transaction Reporting Office as soon as practicable.",
                "applicability": "When suspicion arises",
                "deadline": "As soon as practicable",
                "penalty": "Fine up to SGD 20,000 or imprisonment up to 2 years"
            },
            {
                "regulation_id": "MAS-626-§19.1",
                "jurisdiction": "SG",
                "authority": "MAS",
                "section": "§ 19.1",
                "title": "Record Keeping",
                "content": "Financial institutions shall maintain records of transactions for at least 5 years after business relations end or after occasional transaction date. Records must enable individual transactions to be reconstructed and provide evidence in prosecutions.",
                "applicability": "All transactions and relationships",
                "deadline": "5 years retention",
                "penalty": "Penalties for non-compliance"
            },
            {
                "regulation_id": "MAS-626-§7.4",
                "jurisdiction": "SG",
                "authority": "MAS",
                "section": "§ 7.4",
                "title": "Beneficial Ownership for Legal Persons",
                "content": "When customer is a legal person, financial institution shall identify beneficial owners and take reasonable measures to verify. Beneficial owner means natural person who ultimately owns or controls the legal person through ownership of shares, voting rights, or other means.",
                "applicability": "All corporate customers",
                "deadline": "At relationship establishment",
                "penalty": "Administrative penalties"
            },
            {
                "regulation_id": "MAS-626-§13.1",
                "jurisdiction": "SG",
                "authority": "MAS",
                "section": "§ 13.1",
                "title": "Ongoing Monitoring and Scrutiny",
                "content": "Financial institutions shall conduct ongoing monitoring of business relationships including scrutiny of transactions to ensure consistency with knowledge of customer and business risk profile. Institutions must keep customer information and documents up-to-date through periodic reviews.",
                "applicability": "All ongoing relationships",
                "deadline": "Continuous",
                "penalty": "Regulatory sanctions"
            },
            {
                "regulation_id": "MAS-626-§12.1",
                "jurisdiction": "SG",
                "authority": "MAS",
                "section": "§ 12.1",
                "title": "Correspondent Banking Relationships",
                "content": "Financial institutions shall, in relation to cross-border correspondent banking relationships, gather information about respondent institution, assess ML/TF controls, obtain approval from senior management, and document respective AML/CFT responsibilities.",
                "applicability": "Cross-border correspondent banking",
                "deadline": "Before establishing relationship",
                "penalty": "Relationship termination may be required"
            },
            {
                "regulation_id": "MAS-626-§21.1",
                "jurisdiction": "SG",
                "authority": "MAS",
                "section": "§ 21.1",
                "title": "Internal Policies and Procedures",
                "content": "Financial institutions shall develop and implement internal policies, procedures and controls approved by senior management. These must include customer acceptance policies, risk management practices, monitoring and reporting suspicious transactions, and record keeping.",
                "applicability": "Enterprise-wide",
                "deadline": "Ongoing maintenance",
                "penalty": "Regulatory review and sanctions"
            },
            {
                "regulation_id": "MAS-626-§23.1",
                "jurisdiction": "SG",
                "authority": "MAS",
                "section": "§ 23.1",
                "title": "Screening Against Designated Lists",
                "content": "Financial institutions shall screen customers, connected parties and beneficial owners against lists of designated individuals and entities. Screening must occur before establishing relations, at periodic intervals, and when lists are updated.",
                "applicability": "All customers and transactions",
                "deadline": "Before relationship and periodically",
                "penalty": "Serious violations may result in criminal prosecution"
            },
            {
                "regulation_id": "MAS-626-§22.1",
                "jurisdiction": "SG",
                "authority": "MAS",
                "section": "§ 22.1",
                "title": "Staff Training and Awareness",
                "content": "Financial institutions shall take steps to ensure relevant employees are regularly trained on ML/TF risks, AML/CFT laws, and internal policies. Training programs must be ongoing and targeted to different roles.",
                "applicability": "All relevant staff",
                "deadline": "Regular ongoing training",
                "penalty": "Training deficiencies subject to enforcement"
            }
        ]
        return regulations

    def generate_fincen_regulations(self) -> List[Dict]:
        """
        Generate FinCEN BSA/AML Requirements (US)
        """
        regulations = [
            {
                "regulation_id": "FinCEN-31CFR-§103.18",
                "jurisdiction": "US",
                "authority": "FinCEN",
                "section": "31 CFR § 103.18",
                "title": "Suspicious Activity Report Filing Requirements",
                "content": "A financial institution must file a Suspicious Activity Report (SAR) when it detects transactions aggregating USD 5,000 or more where the institution knows, suspects, or has reason to suspect the transaction involves funds from illegal activity, is designed to evade BSA requirements, or has no business or lawful purpose.",
                "applicability": "Suspicious transactions above USD 5,000",
                "deadline": "Within 30 calendar days of initial detection",
                "penalty": "Civil penalties up to USD 100,000 per violation"
            },
            {
                "regulation_id": "FinCEN-31CFR-§103.121",
                "jurisdiction": "US",
                "authority": "FinCEN",
                "section": "31 CFR § 103.121",
                "title": "Customer Identification Program",
                "content": "Banks must implement a Customer Identification Program (CIP) that includes risk-based procedures for verifying customer identity, including name, date of birth, address, and identification number. Verification must occur within reasonable time before or after account opening.",
                "applicability": "All new account openings",
                "deadline": "Within reasonable time of account opening",
                "penalty": "Civil money penalties"
            },
            {
                "regulation_id": "FinCEN-31CFR-§103.33",
                "jurisdiction": "US",
                "authority": "FinCEN",
                "section": "31 CFR § 103.33",
                "title": "Currency Transaction Reports",
                "content": "Financial institutions must file Currency Transaction Reports (CTR) for currency transactions exceeding USD 10,000 conducted by or on behalf of one person in one business day. Multiple transactions must be treated as single transaction if institution has knowledge they are by or on behalf of same person.",
                "applicability": "Currency transactions over USD 10,000",
                "deadline": "Within 15 days of transaction",
                "penalty": "Civil and criminal penalties"
            },
            {
                "regulation_id": "FinCEN-31CFR-§103.175",
                "jurisdiction": "US",
                "authority": "FinCEN",
                "section": "31 CFR § 103.175",
                "title": "Prohibition on Structuring Transactions",
                "content": "No person shall structure or attempt to structure transactions to evade CTR filing requirements. Structuring means conducting transactions in amounts below reporting thresholds for purpose of evading reporting. Financial institutions must identify and report structuring.",
                "applicability": "All transactions",
                "deadline": "Ongoing monitoring",
                "penalty": "Criminal penalties including imprisonment"
            },
            {
                "regulation_id": "FinCEN-31CFR-§103.122",
                "jurisdiction": "US",
                "authority": "FinCEN",
                "section": "31 CFR § 103.122",
                "title": "Customer Due Diligence Requirements",
                "content": "Banks must establish and maintain written procedures reasonably designed to identify and verify beneficial owners of legal entity customers, understand nature and purpose of customer relationships, and conduct ongoing monitoring to identify and report suspicious transactions.",
                "applicability": "Legal entity customers",
                "deadline": "At account opening",
                "penalty": "Regulatory enforcement actions"
            },
            {
                "regulation_id": "FinCEN-31CFR-§103.130",
                "jurisdiction": "US",
                "authority": "FinCEN",
                "section": "31 CFR § 103.130",
                "title": "BSA Compliance Program Requirement",
                "content": "Banks must develop and implement a written BSA compliance program approved by board of directors. Program must include internal controls, independent testing, designated BSA officer, and training for appropriate personnel.",
                "applicability": "All covered institutions",
                "deadline": "Ongoing maintenance",
                "penalty": "Civil money penalties"
            },
            {
                "regulation_id": "FinCEN-31CFR-§103.178",
                "jurisdiction": "US",
                "authority": "FinCEN",
                "section": "31 CFR § 103.178",
                "title": "Prohibition Against Informal Value Transfer Systems",
                "content": "No person may operate an informal value transfer system unless registered with FinCEN as a money services business. Institutions must not facilitate underground or unregistered remittance systems commonly known as hawalas or other informal value transfer systems.",
                "applicability": "Money services businesses",
                "deadline": "Registration required before operations",
                "penalty": "Criminal and civil penalties"
            },
            {
                "regulation_id": "FinCEN-31CFR-§103.140",
                "jurisdiction": "US",
                "authority": "FinCEN",
                "section": "31 CFR § 103.140",
                "title": "Suspicious Activity Report Confidentiality",
                "content": "SARs and information that would reveal the existence of a SAR are confidential. No financial institution or person may notify any person involved in the transaction that the transaction has been reported. Violations may result in civil and criminal penalties.",
                "applicability": "All SAR filings",
                "deadline": "Indefinite confidentiality",
                "penalty": "Criminal penalties including imprisonment"
            },
            {
                "regulation_id": "FinCEN-31CFR-§103.131",
                "jurisdiction": "US",
                "authority": "FinCEN",
                "section": "31 CFR § 103.131",
                "title": "Correspondent Accounts for Foreign Banks",
                "content": "Banks must establish due diligence program for correspondent accounts for foreign financial institutions. Program must include determining ownership, management, AML program quality, and purpose of correspondent account. Enhanced due diligence required for higher-risk accounts.",
                "applicability": "Correspondent banking for foreign institutions",
                "deadline": "Before establishing account",
                "penalty": "Account termination may be required"
            },
            {
                "regulation_id": "FinCEN-31CFR-§103.137",
                "jurisdiction": "US",
                "authority": "FinCEN",
                "section": "31 CFR § 103.137",
                "title": "Private Banking Due Diligence",
                "content": "Banks offering private banking accounts to non-US persons must establish due diligence program including determining whether account holder is senior foreign political figure, source of funds, and beneficial ownership. Enhanced scrutiny required for senior foreign political figures.",
                "applicability": "Private banking for non-US persons",
                "deadline": "At account opening",
                "penalty": "Regulatory sanctions"
            }
        ]
        return regulations

    def generate_fatf_regulations(self) -> List[Dict]:
        """
        Generate FATF 40 Recommendations excerpts
        """
        regulations = [
            {
                "regulation_id": "FATF-R10",
                "jurisdiction": "INT",
                "authority": "FATF",
                "section": "Recommendation 10",
                "title": "Customer Due Diligence",
                "content": "Financial institutions should be required to undertake customer due diligence measures when establishing business relations, carrying out occasional transactions above threshold, when there is suspicion of money laundering or terrorist financing, or when doubts exist about previously obtained identification data. CDD includes identifying and verifying customer identity, beneficial owner, understanding purpose and nature of relationship, and conducting ongoing monitoring.",
                "applicability": "Universal standard for all jurisdictions",
                "deadline": "Varies by jurisdiction implementation",
                "penalty": "National implementation varies"
            },
            {
                "regulation_id": "FATF-R20",
                "jurisdiction": "INT",
                "authority": "FATF",
                "section": "Recommendation 20",
                "title": "Reporting of Suspicious Transactions",
                "content": "If a financial institution suspects or has reasonable grounds to suspect that funds are the proceeds of criminal activity, or are related to terrorist financing, it should be required to report promptly its suspicions to the financial intelligence unit (FIU). Financial institutions and their employees should be protected by law from criminal and civil liability for breach of confidentiality for reporting in good faith.",
                "applicability": "All financial institutions globally",
                "deadline": "Promptly upon suspicion",
                "penalty": "Varies by jurisdiction"
            },
            {
                "regulation_id": "FATF-R6",
                "jurisdiction": "INT",
                "authority": "FATF",
                "section": "Recommendation 6",
                "title": "Targeted Financial Sanctions - Terrorism & Terrorist Financing",
                "content": "Countries should implement targeted financial sanctions to comply with UN Security Council resolutions relating to prevention and suppression of terrorism and terrorist financing. This includes freezing without delay funds or assets of designated persons and entities, prohibiting making funds available to designated persons, and having mechanisms to examine and give effect to freezing actions of other jurisdictions.",
                "applicability": "All UN member states",
                "deadline": "Without delay upon designation",
                "penalty": "International sanctions"
            },
            {
                "regulation_id": "FATF-R15",
                "jurisdiction": "INT",
                "authority": "FATF",
                "section": "Recommendation 15",
                "title": "New Technologies",
                "content": "Countries and financial institutions should identify and assess money laundering or terrorist financing risks that may arise in relation to development of new products and new business practices, including new delivery mechanisms, and use of new or developing technologies for both new and pre-existing products. Risk assessments should be conducted prior to launch or use of new products, practices and technologies.",
                "applicability": "All new technology implementations",
                "deadline": "Prior to launch",
                "penalty": "Jurisdictional enforcement"
            },
            {
                "regulation_id": "FATF-R1",
                "jurisdiction": "INT",
                "authority": "FATF",
                "section": "Recommendation 1",
                "title": "Risk Assessment and Risk-Based Approach",
                "content": "Countries should identify, assess, and understand money laundering and terrorist financing risks for the country, and should take action to ensure national AML/CFT policies are directed towards mitigating these risks. Financial institutions should identify, assess and take effective action to mitigate their ML/TF risks in relation to customers, countries, products, services, transactions and delivery channels.",
                "applicability": "National and institutional level",
                "deadline": "Ongoing",
                "penalty": "FATF mutual evaluation consequences"
            }
        ]
        return regulations

    def generate_all_regulations(self) -> List[Dict]:
        """
        Generate all regulatory texts
        """
        print("Generating 15 HKMA regulations...")
        self.generated_regulations.extend(self.generate_hkma_regulations())

        print("Generating 10 MAS regulations...")
        self.generated_regulations.extend(self.generate_mas_regulations())

        print("Generating 10 FinCEN regulations...")
        self.generated_regulations.extend(self.generate_fincen_regulations())

        print("Generating 5 FATF recommendations...")
        self.generated_regulations.extend(self.generate_fatf_regulations())

        print(f"✓ Generated {len(self.generated_regulations)} total regulations")
        return self.generated_regulations

    def save_to_file(self, output_path: Path):
        """Save generated regulations to JSON file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.generated_regulations, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved to {output_path}")


def main():
    """Main execution function"""
    print("=" * 70)
    print("  Regulatory Text Generator")
    print("=" * 70)

    generator = RegulationGenerator()
    regulations = generator.generate_all_regulations()

    # Save to seeds directory
    output_path = Path(__file__).parent.parent / "seeds" / "regulations.json"
    generator.save_to_file(output_path)

    # Print summary
    print("\n" + "=" * 70)
    print("  Summary")
    print("=" * 70)
    print(f"  Total Regulations: {len(regulations)}")
    print(f"  HKMA: {sum(1 for r in regulations if r['authority'] == 'HKMA')}")
    print(f"  MAS: {sum(1 for r in regulations if r['authority'] == 'MAS')}")
    print(f"  FinCEN: {sum(1 for r in regulations if r['authority'] == 'FinCEN')}")
    print(f"  FATF: {sum(1 for r in regulations if r['authority'] == 'FATF')}")
    print()


if __name__ == "__main__":
    main()
