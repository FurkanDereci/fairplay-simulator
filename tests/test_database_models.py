import unittest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.backend.models.database import Base, UserModel, UserBalanceModel, CooldownStateModel, WagerModel, NAVHistoryModel

class TestDatabaseModels(unittest.TestCase):
    def setUp(self):
        # In-memory SQLite for fast, isolated test execution
        self.engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False})
        Base.metadata.create_all(bind=self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_user_creation_with_related_models(self):
        user = UserModel(
            email='investor@fairplay.com',
            username='trader_one',
            password_hash='hashed_pw_secret'
        )
        self.session.add(user)
        self.session.commit()

        balance = UserBalanceModel(user_id=user.id, cash_balance=1500.0, locked_stakes=200.0, total_units=15.0)
        cooldown = CooldownStateModel(user_id=user.id, current_tier=0, status='ACTIVE')
        wager = WagerModel(
            user_id=user.id,
            match_id='match_101',
            league='Premier League',
            match_title='Arsenal vs Chelsea',
            market_type='1X2',
            selection='HOME',
            stake=200.0,
            odds=1.95,
            potential_payout=390.0,
            status='PENDING'
        )
        nav_entry = NAVHistoryModel(
            user_id=user.id,
            series_id=1,
            nav=100.0,
            cash_balance=1500.0,
            locked_stakes=200.0,
            total_units=15.0,
            tx_type='INITIAL_DEPOSIT',
            amount=1500.0
        )

        self.session.add_all([balance, cooldown, wager, nav_entry])
        self.session.commit()

        # Query user and check relations
        queried = self.session.query(UserModel).filter_by(username='trader_one').first()
        self.assertIsNotNone(queried)
        self.assertEqual(queried.balance.cash_balance, 1500.0)
        self.assertEqual(queried.cooldown.status, 'ACTIVE')
        self.assertEqual(len(queried.wagers), 1)
        self.assertEqual(queried.wagers[0].selection, 'HOME')
        self.assertEqual(len(queried.nav_history), 1)
        self.assertEqual(queried.nav_history[0].tx_type, 'INITIAL_DEPOSIT')

    def test_cascade_delete_removes_user_records(self):
        user = UserModel(
            email='delete_me@fairplay.com',
            username='delete_me',
            password_hash='dummy_hash'
        )
        self.session.add(user)
        self.session.commit()

        balance = UserBalanceModel(user_id=user.id)
        wager = WagerModel(
            user_id=user.id,
            match_id='m1',
            market_type='1X2',
            selection='AWAY',
            stake=50.0,
            odds=3.0,
            potential_payout=150.0
        )
        self.session.add_all([balance, wager])
        self.session.commit()

        # Delete user
        self.session.delete(user)
        self.session.commit()

        # Verify cascades
        self.assertIsNone(self.session.query(UserModel).filter_by(username='delete_me').first())
        self.assertIsNone(self.session.query(UserBalanceModel).filter_by(user_id=user.id).first())
        self.assertEqual(self.session.query(WagerModel).filter_by(user_id=user.id).count(), 0)

if __name__ == '__main__':
    unittest.main()
