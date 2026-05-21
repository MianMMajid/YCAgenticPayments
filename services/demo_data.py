"""Demo data used when the app runs without external service credentials."""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from models.settlement import BlockchainEvent
from models.payment import Payment, PaymentStatus, PaymentType
from models.transaction import Transaction, TransactionState
from models.user import User
from models.verification import TaskStatus, VerificationTask, VerificationType


DEMO_USER_ID = "demo_user"

DEMO_PROPERTIES: List[Dict[str, Any]] = [
    {
        "property_id": "demo-guilford-567",
        "address": "567 Guilford Avenue, Baltimore, MD",
        "price": 395000,
        "beds": 4,
        "baths": 2,
        "sqft": 2140,
        "summary": (
            "Strong rent-to-value profile with electrical and title items ready "
            "for expert review."
        ),
        "listing_url": None,
    },
    {
        "property_id": "demo-monument-123",
        "address": "123 Monument Street, Baltimore, MD",
        "price": 370000,
        "beds": 3,
        "baths": 2,
        "sqft": 1880,
        "summary": (
            "Clean diligence posture with zoning aligned to residential use and "
            "comps near offer price."
        ),
        "listing_url": None,
    },
    {
        "property_id": "demo-fort-914",
        "address": "914 Fort Avenue, Baltimore, MD",
        "price": 425000,
        "beds": 4,
        "baths": 3,
        "sqft": 2360,
        "summary": (
            "Higher-upside candidate with appraisal variance and geospatial "
            "constraints requiring review."
        ),
        "listing_url": None,
    },
    {
        "property_id": "demo-canton-220",
        "address": "220 Canton Row, Baltimore, MD",
        "price": 515000,
        "beds": 3,
        "baths": 3,
        "sqft": 2410,
        "summary": (
            "Settlement-ready rowhome with clean title, complete appraisal, and "
            "approved repair credit."
        ),
        "listing_url": None,
    },
    {
        "property_id": "demo-charles-808",
        "address": "808 North Charles Street, Baltimore, MD",
        "price": 610000,
        "beds": 5,
        "baths": 4,
        "sqft": 3680,
        "summary": (
            "Complex mixed-use diligence file with zoning, lease, and lender "
            "conditions still under review."
        ),
        "listing_url": None,
    },
    {
        "property_id": "demo-remington-41",
        "address": "41 Remington Avenue, Baltimore, MD",
        "price": 289000,
        "beds": 3,
        "baths": 1.5,
        "sqft": 1510,
        "summary": (
            "Cancelled deal candidate showing failed inspection and returned "
            "earnest-money workflow."
        ),
        "listing_url": None,
    },
]

DEMO_RISK_BY_PROPERTY: Dict[str, Dict[str, Any]] = {
    "demo-guilford-567": {
        "overall_risk": "medium",
        "data_sources": {"rentcast": True, "fema": True, "crime": True},
        "flags": [
            {
                "severity": "medium",
                "category": "inspection",
                "message": "Electrical panel exception needs buyer approval before payment release.",
                "details": {"document": "Inspection report.pdf"},
            },
            {
                "severity": "low",
                "category": "title",
                "message": "Recorded utility easement should be cited in the final memo.",
                "details": {"document": "Title exceptions.pdf"},
            },
        ],
    },
    "demo-monument-123": {
        "overall_risk": "low",
        "data_sources": {"rentcast": True, "fema": True, "crime": True},
        "flags": [
            {
                "severity": "low",
                "category": "valuation",
                "message": "Offer price is within the comparable-sale range after bedroom adjustment.",
                "details": {"comps": 3},
            }
        ],
    },
    "demo-fort-914": {
        "overall_risk": "high",
        "data_sources": {"rentcast": True, "fema": True, "crime": False},
        "flags": [
            {
                "severity": "high",
                "category": "flood",
                "message": "Flood overlay proximity requires map confirmation and insurance review.",
                "details": {"flood_zone": "AE proximity"},
            },
            {
                "severity": "medium",
                "category": "permits",
                "message": "Renovation permit history is incomplete for the lower-level conversion.",
                "details": {"missing_document": "final inspection signoff"},
            },
        ],
    },
    "demo-canton-220": {
        "overall_risk": "low",
        "data_sources": {"rentcast": True, "fema": True, "crime": True},
        "flags": [
            {
                "severity": "low",
                "category": "closing",
                "message": "All required diligence items are approved and ready for settlement.",
                "details": {"approval_count": 4},
            }
        ],
    },
    "demo-charles-808": {
        "overall_risk": "high",
        "data_sources": {"rentcast": True, "fema": True, "crime": True},
        "flags": [
            {
                "severity": "high",
                "category": "zoning",
                "message": "Mixed-use certificate conflicts with the intended residential-only underwriting case.",
                "details": {"document": "Zoning certificate.pdf"},
            },
            {
                "severity": "medium",
                "category": "leases",
                "message": "Two tenant estoppels are missing from the uploaded diligence package.",
                "details": {"missing_documents": 2},
            },
        ],
    },
    "demo-remington-41": {
        "overall_risk": "high",
        "data_sources": {"rentcast": True, "fema": False, "crime": True},
        "flags": [
            {
                "severity": "high",
                "category": "inspection",
                "message": "Structural inspection failed and buyer elected to cancel before release.",
                "details": {"document": "Structural inspection.pdf"},
            }
        ],
    },
}


def demo_search_results() -> tuple[List[Dict[str, Any]], int]:
    """Return deterministic property search results for local demo mode."""
    return DEMO_PROPERTIES, len(DEMO_PROPERTIES)


def demo_risk_response(property_id: str, address: str, list_price: int) -> Dict[str, Any]:
    """Return deterministic risk analysis for local demo mode."""
    if property_id in DEMO_RISK_BY_PROPERTY:
        return DEMO_RISK_BY_PROPERTY[property_id]

    return {
        "overall_risk": "medium",
        "data_sources": {"rentcast": False, "fema": False, "crime": False},
        "flags": [
            {
                "severity": "medium",
                "category": "data",
                "message": (
                    f"{address} at ${list_price:,} needs live data enrichment before "
                    "a final diligence recommendation."
                ),
                "details": {"property_id": property_id},
            }
        ],
    }


def seed_demo_data(db: Session) -> None:
    """Create a coherent local transaction graph for the frontend workflow."""
    now = datetime.utcnow()

    if not db.query(User).filter(User.id == DEMO_USER_ID).first():
        db.add(
            User(
                id=DEMO_USER_ID,
                phone_number="+15550000000",
                email="demo@example.com",
                name="Demo Buyer",
                preferred_locations=["Baltimore, MD"],
                max_budget=450000,
                min_beds=3,
                min_baths=2,
                pre_approved=True,
                pre_approval_amount=450000,
                last_active=now.isoformat(),
            )
        )

    transactions = [
        Transaction(
            id="demo-transaction-guilford",
            buyer_agent_id="buyer-agent-demo",
            seller_agent_id="seller-agent-rail",
            property_id="demo-guilford-567",
            earnest_money=Decimal("10000.00"),
            total_purchase_price=Decimal("395000.00"),
            state=TransactionState.VERIFICATION_IN_PROGRESS,
            wallet_id="wallet-demo-guilford",
            initiated_at=now - timedelta(days=3),
            target_closing_date=now + timedelta(days=21),
            transaction_metadata={
                "address": "567 Guilford Avenue, Baltimore, MD",
                "market": "Baltimore, MD",
            },
        ),
        Transaction(
            id="demo-transaction-monument",
            buyer_agent_id="buyer-agent-demo",
            seller_agent_id="seller-agent-harbor",
            property_id="demo-monument-123",
            earnest_money=Decimal("9000.00"),
            total_purchase_price=Decimal("370000.00"),
            state=TransactionState.FUNDED,
            wallet_id="wallet-demo-monument",
            initiated_at=now - timedelta(days=1),
            target_closing_date=now + timedelta(days=28),
            transaction_metadata={
                "address": "123 Monument Street, Baltimore, MD",
                "market": "Baltimore, MD",
            },
        ),
        Transaction(
            id="demo-transaction-fort",
            buyer_agent_id="buyer-agent-demo",
            seller_agent_id="seller-agent-waterfront",
            property_id="demo-fort-914",
            earnest_money=Decimal("12000.00"),
            total_purchase_price=Decimal("425000.00"),
            state=TransactionState.DISPUTED,
            wallet_id="wallet-demo-fort",
            initiated_at=now - timedelta(days=8),
            target_closing_date=now + timedelta(days=14),
            transaction_metadata={
                "address": "914 Fort Avenue, Baltimore, MD",
                "market": "Baltimore, MD",
            },
        ),
        Transaction(
            id="demo-transaction-canton",
            buyer_agent_id="buyer-agent-demo",
            seller_agent_id="seller-agent-canton",
            property_id="demo-canton-220",
            earnest_money=Decimal("15000.00"),
            total_purchase_price=Decimal("515000.00"),
            state=TransactionState.SETTLED,
            wallet_id="wallet-demo-canton",
            initiated_at=now - timedelta(days=19),
            target_closing_date=now - timedelta(days=1),
            actual_closing_date=now - timedelta(hours=18),
            transaction_metadata={
                "address": "220 Canton Row, Baltimore, MD",
                "market": "Baltimore, MD",
            },
        ),
        Transaction(
            id="demo-transaction-charles",
            buyer_agent_id="buyer-agent-demo",
            seller_agent_id="seller-agent-midtown",
            property_id="demo-charles-808",
            earnest_money=Decimal("20000.00"),
            total_purchase_price=Decimal("610000.00"),
            state=TransactionState.SETTLEMENT_PENDING,
            wallet_id="wallet-demo-charles",
            initiated_at=now - timedelta(days=11),
            target_closing_date=now + timedelta(days=6),
            transaction_metadata={
                "address": "808 North Charles Street, Baltimore, MD",
                "market": "Baltimore, MD",
            },
        ),
        Transaction(
            id="demo-transaction-remington",
            buyer_agent_id="buyer-agent-demo",
            seller_agent_id="seller-agent-remington",
            property_id="demo-remington-41",
            earnest_money=Decimal("6000.00"),
            total_purchase_price=Decimal("289000.00"),
            state=TransactionState.CANCELLED,
            wallet_id="wallet-demo-remington",
            initiated_at=now - timedelta(days=6),
            target_closing_date=now + timedelta(days=20),
            actual_closing_date=now - timedelta(days=2),
            transaction_metadata={
                "address": "41 Remington Avenue, Baltimore, MD",
                "market": "Baltimore, MD",
            },
        ),
    ]
    db.add_all([
        transaction
        for transaction in transactions
        if not db.query(Transaction).filter(Transaction.id == transaction.id).first()
    ])

    tasks = [
        VerificationTask(
            id="task-title-guilford",
            transaction_id="demo-transaction-guilford",
            verification_type=VerificationType.TITLE_SEARCH,
            assigned_agent_id="title-agent-landamerica",
            status=TaskStatus.COMPLETED,
            deadline=now + timedelta(days=2),
            payment_amount=Decimal("1200.00"),
            assigned_at=now - timedelta(days=3),
            completed_at=now - timedelta(days=1),
        ),
        VerificationTask(
            id="task-inspection-guilford",
            transaction_id="demo-transaction-guilford",
            verification_type=VerificationType.INSPECTION,
            assigned_agent_id="inspection-agent-amerispec",
            status=TaskStatus.IN_PROGRESS,
            deadline=now + timedelta(days=4),
            payment_amount=Decimal("500.00"),
            assigned_at=now - timedelta(days=2),
        ),
        VerificationTask(
            id="task-appraisal-guilford",
            transaction_id="demo-transaction-guilford",
            verification_type=VerificationType.APPRAISAL,
            assigned_agent_id="appraisal-agent-corelogic",
            status=TaskStatus.ASSIGNED,
            deadline=now + timedelta(days=5),
            payment_amount=Decimal("400.00"),
            assigned_at=now - timedelta(days=1),
        ),
        VerificationTask(
            id="task-title-fort",
            transaction_id="demo-transaction-fort",
            verification_type=VerificationType.TITLE_SEARCH,
            assigned_agent_id="title-agent-landamerica",
            status=TaskStatus.COMPLETED,
            deadline=now - timedelta(days=2),
            payment_amount=Decimal("1200.00"),
            assigned_at=now - timedelta(days=8),
            completed_at=now - timedelta(days=4),
        ),
        VerificationTask(
            id="task-inspection-fort",
            transaction_id="demo-transaction-fort",
            verification_type=VerificationType.INSPECTION,
            assigned_agent_id="inspection-agent-amerispec",
            status=TaskStatus.FAILED,
            deadline=now - timedelta(days=1),
            payment_amount=Decimal("500.00"),
            assigned_at=now - timedelta(days=8),
            completed_at=now - timedelta(days=2),
        ),
        VerificationTask(
            id="task-appraisal-canton",
            transaction_id="demo-transaction-canton",
            verification_type=VerificationType.APPRAISAL,
            assigned_agent_id="appraisal-agent-corelogic",
            status=TaskStatus.COMPLETED,
            deadline=now - timedelta(days=5),
            payment_amount=Decimal("400.00"),
            assigned_at=now - timedelta(days=17),
            completed_at=now - timedelta(days=9),
        ),
        VerificationTask(
            id="task-lending-canton",
            transaction_id="demo-transaction-canton",
            verification_type=VerificationType.LENDING,
            assigned_agent_id="lending-agent-fanniemae",
            status=TaskStatus.COMPLETED,
            deadline=now - timedelta(days=2),
            payment_amount=Decimal("0.00"),
            assigned_at=now - timedelta(days=17),
            completed_at=now - timedelta(days=3),
        ),
        VerificationTask(
            id="task-title-charles",
            transaction_id="demo-transaction-charles",
            verification_type=VerificationType.TITLE_SEARCH,
            assigned_agent_id="title-agent-landamerica",
            status=TaskStatus.COMPLETED,
            deadline=now - timedelta(days=1),
            payment_amount=Decimal("1200.00"),
            assigned_at=now - timedelta(days=10),
            completed_at=now - timedelta(days=4),
        ),
        VerificationTask(
            id="task-lending-charles",
            transaction_id="demo-transaction-charles",
            verification_type=VerificationType.LENDING,
            assigned_agent_id="lending-agent-fanniemae",
            status=TaskStatus.IN_PROGRESS,
            deadline=now + timedelta(days=3),
            payment_amount=Decimal("0.00"),
            assigned_at=now - timedelta(days=9),
        ),
        VerificationTask(
            id="task-inspection-remington",
            transaction_id="demo-transaction-remington",
            verification_type=VerificationType.INSPECTION,
            assigned_agent_id="inspection-agent-amerispec",
            status=TaskStatus.FAILED,
            deadline=now - timedelta(days=3),
            payment_amount=Decimal("500.00"),
            assigned_at=now - timedelta(days=6),
            completed_at=now - timedelta(days=3),
        ),
    ]
    db.add_all([
        task
        for task in tasks
        if not db.query(VerificationTask).filter(VerificationTask.id == task.id).first()
    ])

    payments = [
        Payment(
            id="payment-earnest-guilford",
            transaction_id="demo-transaction-guilford",
            wallet_id="wallet-demo-guilford",
            payment_type=PaymentType.EARNEST_MONEY,
            recipient_id="escrow-wallet",
            amount=Decimal("10000.00"),
            status=PaymentStatus.COMPLETED,
            blockchain_tx_hash="0xdemoearnest567",
            initiated_at=now - timedelta(days=3),
            completed_at=now - timedelta(days=3, minutes=-2),
        ),
        Payment(
            id="payment-title-guilford",
            transaction_id="demo-transaction-guilford",
            wallet_id="wallet-demo-guilford",
            payment_type=PaymentType.VERIFICATION,
            recipient_id="title-agent-landamerica",
            amount=Decimal("1200.00"),
            status=PaymentStatus.COMPLETED,
            blockchain_tx_hash="0xdempotitle567",
            initiated_at=now - timedelta(days=1),
            completed_at=now - timedelta(days=1, minutes=-3),
        ),
        Payment(
            id="payment-inspection-guilford",
            transaction_id="demo-transaction-guilford",
            wallet_id="wallet-demo-guilford",
            payment_type=PaymentType.VERIFICATION,
            recipient_id="inspection-agent-amerispec",
            amount=Decimal("500.00"),
            status=PaymentStatus.PENDING,
            initiated_at=now,
        ),
        Payment(
            id="payment-earnest-monument",
            transaction_id="demo-transaction-monument",
            wallet_id="wallet-demo-monument",
            payment_type=PaymentType.EARNEST_MONEY,
            recipient_id="escrow-wallet",
            amount=Decimal("9000.00"),
            status=PaymentStatus.COMPLETED,
            blockchain_tx_hash="0xdemoearnest123",
            initiated_at=now - timedelta(days=1),
            completed_at=now - timedelta(days=1, minutes=-2),
        ),
        Payment(
            id="payment-dispute-fort",
            transaction_id="demo-transaction-fort",
            wallet_id="wallet-demo-fort",
            payment_type=PaymentType.VERIFICATION,
            recipient_id="inspection-agent-amerispec",
            amount=Decimal("500.00"),
            status=PaymentStatus.FAILED,
            blockchain_tx_hash="0xdemoinspectfailed914",
            initiated_at=now - timedelta(days=2),
            completed_at=now - timedelta(days=2, minutes=-4),
        ),
        Payment(
            id="payment-settlement-canton",
            transaction_id="demo-transaction-canton",
            wallet_id="wallet-demo-canton",
            payment_type=PaymentType.SETTLEMENT,
            recipient_id="seller-agent-canton",
            amount=Decimal("500000.00"),
            status=PaymentStatus.COMPLETED,
            blockchain_tx_hash="0xdemosettled220",
            initiated_at=now - timedelta(hours=20),
            completed_at=now - timedelta(hours=18),
        ),
        Payment(
            id="payment-title-charles",
            transaction_id="demo-transaction-charles",
            wallet_id="wallet-demo-charles",
            payment_type=PaymentType.VERIFICATION,
            recipient_id="title-agent-landamerica",
            amount=Decimal("1200.00"),
            status=PaymentStatus.COMPLETED,
            blockchain_tx_hash="0xdemotitle808",
            initiated_at=now - timedelta(days=4),
            completed_at=now - timedelta(days=4, minutes=-2),
        ),
        Payment(
            id="payment-refund-remington",
            transaction_id="demo-transaction-remington",
            wallet_id="wallet-demo-remington",
            payment_type=PaymentType.EARNEST_MONEY,
            recipient_id="buyer-agent-demo",
            amount=Decimal("6000.00"),
            status=PaymentStatus.COMPLETED,
            blockchain_tx_hash="0xdemorefund41",
            initiated_at=now - timedelta(days=2),
            completed_at=now - timedelta(days=2, minutes=-8),
        ),
    ]
    db.add_all([
        payment
        for payment in payments
        if not db.query(Payment).filter(Payment.id == payment.id).first()
    ])

    events = [
        BlockchainEvent(
            id="event-init-guilford",
            transaction_id="demo-transaction-guilford",
            event_type="transaction_initiated",
            event_data={"property_id": "demo-guilford-567", "source": "demo_seed"},
            blockchain_tx_hash="0xdemo001",
            block_number="210001",
            timestamp=now - timedelta(days=3),
        ),
        BlockchainEvent(
            id="event-funded-guilford",
            transaction_id="demo-transaction-guilford",
            event_type="earnest_money_deposited",
            event_data={"amount": "10000.00", "wallet_id": "wallet-demo-guilford"},
            blockchain_tx_hash="0xdemo002",
            block_number="210014",
            timestamp=now - timedelta(days=3, minutes=-2),
        ),
        BlockchainEvent(
            id="event-title-guilford",
            transaction_id="demo-transaction-guilford",
            event_type="verification_completed",
            event_data={"verification_type": "title_search", "status": "approved"},
            blockchain_tx_hash="0xdemo003",
            block_number="210522",
            timestamp=now - timedelta(days=1),
        ),
        BlockchainEvent(
            id="event-funded-monument",
            transaction_id="demo-transaction-monument",
            event_type="earnest_money_deposited",
            event_data={"amount": "9000.00", "wallet_id": "wallet-demo-monument"},
            blockchain_tx_hash="0xdemo123funded",
            block_number="210404",
            timestamp=now - timedelta(days=1),
        ),
        BlockchainEvent(
            id="event-dispute-fort",
            transaction_id="demo-transaction-fort",
            event_type="dispute_raised",
            event_data={"reason": "inspection_failed", "hold_amount": "12000.00"},
            blockchain_tx_hash="0xdemo914dispute",
            block_number="210610",
            timestamp=now - timedelta(days=2),
        ),
        BlockchainEvent(
            id="event-settlement-canton",
            transaction_id="demo-transaction-canton",
            event_type="settlement_executed",
            event_data={"seller_amount": "500000.00", "status": "complete"},
            blockchain_tx_hash="0xdemo220settled",
            block_number="211020",
            timestamp=now - timedelta(hours=18),
        ),
        BlockchainEvent(
            id="event-ready-charles",
            transaction_id="demo-transaction-charles",
            event_type="settlement_pending",
            event_data={"pending_item": "lender_conditions", "target_close_days": 6},
            blockchain_tx_hash="0xdemo808pending",
            block_number="210888",
            timestamp=now - timedelta(days=1),
        ),
        BlockchainEvent(
            id="event-cancel-remington",
            transaction_id="demo-transaction-remington",
            event_type="transaction_cancelled",
            event_data={"reason": "inspection_contingency", "refund": "6000.00"},
            blockchain_tx_hash="0xdemo41cancel",
            block_number="210711",
            timestamp=now - timedelta(days=2),
        ),
    ]
    db.add_all([
        event
        for event in events
        if not db.query(BlockchainEvent).filter(BlockchainEvent.id == event.id).first()
    ])
    db.commit()
