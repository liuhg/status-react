import random
import string

from support.utilities import get_merged_txs_list
from tests import marks, unique_password, common_password
from tests.base_test_case import SingleDeviceTestCase
from tests.users import transaction_senders, basic_user, wallet_users
from views.send_transaction_view import SendTransactionView
from views.sign_in_view import SignInView


@marks.transaction
class TestTransactionWalletSingleDevice(SingleDeviceTestCase):

    @marks.testrail_id(5308)
    @marks.critical
    def test_send_eth_from_wallet_to_address(self):
        recipient = basic_user
        sender = transaction_senders['P']
        sign_in_view = SignInView(self.driver)
        home_view = sign_in_view.recover_access(sender['passphrase'], password=unique_password)
        wallet_view = home_view.wallet_button.click()
        wallet_view.set_up_wallet()
        wallet_view.accounts_status_account.click()
        send_transaction = wallet_view.send_transaction_button.click()
        send_transaction.amount_edit_box.click()
        transaction_amount = send_transaction.get_unique_amount()
        send_transaction.amount_edit_box.set_value(transaction_amount)
        send_transaction.confirm()
        send_transaction.chose_recipient_button.click()
        send_transaction.enter_recipient_address_button.click()

        send_transaction.just_fyi('Send transaction')
        send_transaction.enter_recipient_address_input.set_value(recipient['address'])
        send_transaction.done_button.click()
        send_transaction.sign_transaction_button.click()
        send_transaction.sign_transaction(unique_password)
        self.network_api.find_transaction_by_unique_amount(sender['address'], transaction_amount)

        send_transaction.just_fyi('Check that transaction is appeared in transaction history')
        transactions_view = wallet_view.transaction_history_button.click()
        transactions_view.transactions_table.find_transaction(amount=transaction_amount)

        transactions_view.just_fyi('Check logcat for sensitive data')
        values_in_logcat = send_transaction.find_values_in_logcat(password=unique_password)
        if values_in_logcat:
            self.driver.fail(values_in_logcat)


    @marks.testrail_id(5408)
    @marks.high
    def test_transaction_wrong_password_wallet(self):
        recipient = basic_user
        sender = wallet_users['A']
        sign_in_view = SignInView(self.driver)
        sign_in_view.recover_access(sender['passphrase'])
        home_view = sign_in_view.get_home_view()
        wallet_view = home_view.wallet_button.click()
        wallet_view.set_up_wallet()
        wallet_view.accounts_status_account.click()
        send_transaction = wallet_view.send_transaction_button.click()
        send_transaction.amount_edit_box.click()
        transaction_amount = send_transaction.get_unique_amount()
        send_transaction.amount_edit_box.set_value(transaction_amount)
        send_transaction.confirm()
        send_transaction.chose_recipient_button.click()
        send_transaction.enter_recipient_address_button.click()
        send_transaction.enter_recipient_address_input.set_value(recipient['address'])
        send_transaction.done_button.click()
        send_transaction.sign_transaction_button.click()
        send_transaction.sign_with_password.click_until_presence_of_element(send_transaction.enter_password_input)
        send_transaction.enter_password_input.click()
        send_transaction.enter_password_input.send_keys('wrong_password')
        send_transaction.sign_button.click()
        if send_transaction.element_by_text_part('Transaction sent').is_element_displayed():
            self.driver.fail('Transaction was sent with a wrong password')

    @marks.testrail_id(6237)
    @marks.high
    def test_fetching_balance_after_offline(self):
        sender = wallet_users['A']
        sign_in_view = SignInView(self.driver)

        sign_in_view.just_fyi('Restore account with funds offline')
        sign_in_view.toggle_airplane_mode()
        sign_in_view.recover_access(sender['passphrase'])
        home_view = sign_in_view.get_home_view()
        wallet_view = home_view.wallet_button.click()
        wallet_view.set_up_wallet()

        sign_in_view.just_fyi('Go back to online and check that balance is updated')
        sign_in_view.toggle_airplane_mode()
        wallet_view.wait_balance_is_changed('ETHro')
        wallet_view.wait_balance_is_changed('STT')

        sign_in_view.just_fyi('Send some tokens to other account')
        recipient = "0x" + basic_user['address']
        sending_amount = wallet_view.get_unique_amount()
        asset = 'STT'
        wallet_view.accounts_status_account.click_until_presence_of_element(wallet_view.send_transaction_button)
        wallet_view.send_transaction(asset_name=asset, amount=sending_amount, recipient=recipient,
                                     sign_transaction=True)
        sign_in_view.toggle_airplane_mode()
        self.network_api.wait_for_confirmation_of_transaction(basic_user['address'], sending_amount, confirmations=6, token=True)

        sign_in_view.just_fyi('Change that balance is updated')
        initial_amount_STT = wallet_view.get_asset_amount_by_name('STT')
        sign_in_view.toggle_airplane_mode()

        sign_in_view.just_fyi('Check that transaction is appeared in transaction history')
        wallet_view.wait_balance_is_changed('STT', initial_amount_STT)
        transactions_view = wallet_view.transaction_history_button.click()
        transactions_view.transactions_table.find_transaction(amount=sending_amount, asset='STT')



    @marks.testrail_id(5461)
    @marks.medium
    def test_send_eth_from_wallet_incorrect_address(self):
        recipient = basic_user
        sender = wallet_users['B']
        sign_in_view = SignInView(self.driver)
        sign_in_view.recover_access(sender['passphrase'])
        home_view = sign_in_view.get_home_view()
        wallet_view = home_view.wallet_button.click()
        wallet_view.set_up_wallet()
        wallet_view.accounts_status_account.click()
        send_transaction = wallet_view.send_transaction_button.click()
        send_transaction.amount_edit_box.click()
        transaction_amount = send_transaction.get_unique_amount()
        send_transaction.amount_edit_box.set_value(transaction_amount)
        send_transaction.confirm()
        send_transaction.chose_recipient_button.click()
        send_transaction.enter_recipient_address_button.click()
        send_transaction.enter_recipient_address_input.set_value(recipient['public_key'])
        send_transaction.done_button.click()
        if not send_transaction.find_text_part('Invalid address'):
            self.errors.append("Invalid address accepted for input as recipient!")
        send_transaction.ok_button.click()
        send_transaction.enter_recipient_address_input.set_value('0xDE709F2102306220921060314715629080E2fB77')
        send_transaction.done_button.click()
        if not send_transaction.element_by_text_part('Invalid address').is_element_displayed():
            self.errors.append('Invalid EIP55 address is resolved correctly')
        send_transaction.ok_button.click()
        self.errors.verify_no_errors()


    @marks.testrail_id(5350)
    @marks.critical
    def test_send_token_with_7_decimals(self):
        sender = transaction_senders['S']
        recipient = basic_user
        sign_in_view = SignInView(self.driver)
        sign_in_view.recover_access(sender['passphrase'])
        home_view = sign_in_view.get_home_view()
        home_view.add_contact(recipient['public_key'])
        home_view.get_back_to_home_view()
        wallet_view = home_view.wallet_button.click()
        wallet_view.set_up_wallet()
        wallet_view.accounts_status_account.click()
        send_transaction = wallet_view.send_transaction_button.click()
        adi_button = send_transaction.asset_by_name('ADI')
        send_transaction.select_asset_button.click_until_presence_of_element(send_transaction.eth_asset_in_select_asset_bottom_sheet_button)
        adi_button.click()
        send_transaction.amount_edit_box.click()
        amount = '0.0%s' % str(random.randint(10000, 99999)) + '1'
        send_transaction.amount_edit_box.set_value(amount)
        send_transaction.confirm()
        send_transaction.chose_recipient_button.click()
        send_transaction.enter_recipient_address_button.click()
        send_transaction.enter_recipient_address_input.set_value(recipient['address'])
        send_transaction.done_button.click()
        send_transaction.sign_transaction_button.click()
        send_transaction.sign_transaction()
        self.network_api.find_transaction_by_unique_amount(recipient['address'], amount, token=True, decimals=7)

    @marks.testrail_id(6245)
    @marks.high
    def test_token_with_more_than_allowed_decimals(self):
        sender = wallet_users['C']
        sign_in_view = SignInView(self.driver)
        sign_in_view.recover_access(sender['passphrase'])
        wallet_view = sign_in_view.wallet_button.click()
        wallet_view.set_up_wallet()
        wallet_view.accounts_status_account.click()
        send_transaction = wallet_view.send_transaction_button.click()
        adi_button = send_transaction.asset_by_name('ADI')
        send_transaction.select_asset_button.click_until_presence_of_element(send_transaction.eth_asset_in_select_asset_bottom_sheet_button)
        adi_button.click()
        send_transaction.amount_edit_box.click()
        amount = '0.0%s' % str(random.randint(100000, 999999)) + '1'
        send_transaction.amount_edit_box.set_value(amount)
        error_text = 'Amount is too precise. Max number of decimals is 7.'
        if not send_transaction.element_by_text(error_text).is_element_displayed():
            self.driver.fail('Warning about too precise amount is not shown when sending a transaction')

    @marks.testrail_id(5423)
    @marks.medium
    def test_send_valid_amount_after_insufficient_funds_error(self):
        sender = transaction_senders['T']
        sign_in_view = SignInView(self.driver)
        sign_in_view.recover_access(sender['passphrase'])
        wallet_view = sign_in_view.wallet_button.click()
        wallet_view.set_up_wallet()
        wallet_view.accounts_status_account.click()
        bigger_amount = wallet_view.get_asset_amount_by_name('ETHro') + 1
        send_transaction = wallet_view.send_transaction_button.click()
        amount_edit_box = send_transaction.amount_edit_box
        amount_edit_box.click()
        amount_edit_box.set_value(bigger_amount)
        send_transaction.element_by_text('Insufficient funds').wait_for_visibility_of_element(5)

        valid_amount = send_transaction.get_unique_amount()
        amount_edit_box.clear()
        amount_edit_box.set_value(valid_amount)
        send_transaction.confirm()
        send_transaction.chose_recipient_button.click()
        send_transaction.enter_recipient_address_button.click()
        send_transaction.enter_recipient_address_input.set_value(basic_user['address'])
        send_transaction.done_button.click()
        send_transaction.sign_transaction_button.click()
        send_transaction.sign_transaction()
        self.network_api.find_transaction_by_unique_amount(sender['address'], valid_amount)

    @marks.testrail_id(5471)
    @marks.medium
    def test_insufficient_funds_wallet_0_balance(self):
        sign_in_view = SignInView(self.driver)
        sign_in_view.create_user()
        wallet_view = sign_in_view.wallet_button.click()
        wallet_view.set_up_wallet()
        wallet_view.select_asset("STT")
        wallet_view.accounts_status_account.click()
        send_transaction = wallet_view.send_transaction_button.click()
        send_transaction.amount_edit_box.set_value(1)
        error_text = send_transaction.element_by_text('Insufficient funds')
        if not error_text.is_element_displayed():
            self.errors.append("'Insufficient funds' error is now shown when sending 1 ETH from wallet with balance 0")
        send_transaction.select_asset_button.click()
        send_transaction.asset_by_name('STT').click()
        send_transaction.amount_edit_box.set_value(1)
        if not error_text.is_element_displayed():
            self.errors.append("'Insufficient funds' error is now shown when sending 1 STT from wallet with balance 0")
        self.errors.verify_no_errors()

    @marks.testrail_id(5412)
    @marks.high
    def test_insufficient_funds_wallet_positive_balance(self):
        sender = wallet_users['E']
        sign_in_view = SignInView(self.driver)
        sign_in_view.recover_access(sender['passphrase'])
        wallet_view = sign_in_view.wallet_button.click()
        wallet_view.set_up_wallet()
        eth_value = wallet_view.get_asset_amount_by_name('ETHro')
        stt_value = wallet_view.get_asset_amount_by_name('STT')
        if eth_value == 0 or stt_value == 0:
            self.driver.fail('No funds!')
        wallet_view.accounts_status_account.click()
        send_transaction = wallet_view.send_transaction_button.click()
        send_transaction.amount_edit_box.set_value(round(eth_value + 1))
        error_text = send_transaction.element_by_text('Insufficient funds')
        if not error_text.is_element_displayed():
            self.errors.append(
                "'Insufficient funds' error is not shown when sending %s ETH from wallet with balance %s" % (
                    round(eth_value + 1), eth_value))
        send_transaction.select_asset_button.click()
        send_transaction.asset_by_name('STT').scroll_to_element()
        send_transaction.asset_by_name('STT').click()
        send_transaction.amount_edit_box.set_value(round(stt_value + 1))
        if not error_text.is_element_displayed():
            self.errors.append(
                "'Insufficient funds' error is not shown when sending %s STT from wallet with balance %s" % (
                    round(stt_value + 1), stt_value))
        self.errors.verify_no_errors()

    @marks.testrail_id(5359)
    @marks.critical
    @marks.skip
    def test_modify_transaction_fee_values(self):
        sender = transaction_senders['U']
        sign_in_view = SignInView(self.driver)
        sign_in_view.recover_access(sender['passphrase'])
        wallet_view = sign_in_view.wallet_button.click()
        wallet_view.set_up_wallet()
        wallet_view.accounts_status_account.click()
        send_transaction = wallet_view.send_transaction_button.click()

        amount = send_transaction.get_unique_amount()
        send_transaction.amount_edit_box.set_value(amount)
        send_transaction.confirm()
        send_transaction.chose_recipient_button.click()
        send_transaction.enter_recipient_address_button.click()
        recipient_address = basic_user['address']
        send_transaction.enter_recipient_address_input.set_value(recipient_address)
        send_transaction.done_button.click()
        send_transaction.sign_transaction_button.click()
        send_transaction.network_fee_button.click_until_presence_of_element(send_transaction.gas_limit_input)
        gas_prices = {
            "1.0000000009": "Invalid number",
            "0.0000000009": "Min 1 wei",
            "-1": "Min 1 wei"
        }
        gas_limit = {
            "20999": "Min 21000 units",
            "21000.1": "Invalid number",
            "-21000": "Min 21000 units"
        }
        for key in gas_prices:
            send_transaction.gas_price_input.clear()
            send_transaction.gas_price_input.send_keys(key)
            if not send_transaction.element_by_text(gas_prices[key]).is_element_displayed():
                self.errors.append("With %s Gas Price value there is no %s error displayed" % key, gas_prices[key])
        send_transaction.gas_price_input.clear()
        send_transaction.gas_price_input.send_keys('10')

        for key in gas_limit:
            send_transaction.gas_price_input.clear()
            send_transaction.gas_price_input.send_keys(key)
            if not send_transaction.element_by_text(gas_limit[key]).is_element_displayed():
                self.errors.append("With %s Gas Limit value there is no %s error displayed" % key, gas_prices[key])
        send_transaction.gas_price_input.clear()
        send_transaction.gas_price_input.send_keys('21000')

        send_transaction.update_fee_button.click_until_absense_of_element(send_transaction.update_fee_button)
        send_transaction.sign_with_password.click_until_presence_of_element(send_transaction.enter_password_input)
        send_transaction.enter_password_input.send_keys(common_password)
        send_transaction.sign_button.click()
        send_transaction.ok_button.click()

    @marks.testrail_id(5314)
    @marks.critical
    def test_can_see_all_transactions_in_history(self):
        address = wallet_users['D']['address']
        passphrase = wallet_users['D']['passphrase']

        ropsten_txs = self.network_api.get_transactions(address)
        ropsten_tokens = self.network_api.get_token_transactions(address)
        expected_txs_list = get_merged_txs_list(ropsten_txs, ropsten_tokens)
        signin_view = SignInView(self.driver)
        home_view = signin_view.recover_access(passphrase=passphrase)
        wallet_view = home_view.wallet_button.click()
        wallet_view.set_up_wallet()
        wallet_view.accounts_status_account.click()
        transaction_view = wallet_view.transaction_history_button.click()

        status_tx_number = transaction_view.transactions_table.get_transactions_number()
        if status_tx_number < 1:
            self.driver.fail('No transactions found')

        for n in range(status_tx_number):
            transactions_details = transaction_view.transactions_table.transaction_by_index(n).click()
            tx_hash = transactions_details.get_transaction_hash()
            tx_from = transactions_details.get_sender_address()
            tx_to = transactions_details.get_recipient_address()
            if tx_from != expected_txs_list[tx_hash]['from']:
                self.errors.append('Transactions senders do not match!')
            if tx_to != expected_txs_list[tx_hash]['to']:
                self.errors.append('Transactions recipients do not match!')
            transactions_details.back_button.click()

        self.errors.verify_no_errors()

    @marks.testrail_id(5429)
    @marks.medium
    def test_set_currency(self):
        sign_in_view = SignInView(self.driver)
        user_currency = 'Euro (EUR)'
        sign_in_view.create_user()
        wallet_view = sign_in_view.wallet_button.click()
        wallet_view.set_currency(user_currency)
        if not wallet_view.find_text_part('EUR'):
            self.driver.fail('EUR currency is not displayed')

    @marks.testrail_id(5407)
    @marks.medium
    def test_cant_send_transaction_in_offline_mode(self):
        sign_in_view = SignInView(self.driver)
        sign_in_view.create_user()
        wallet_view = sign_in_view.wallet_button.click()
        wallet_view.set_up_wallet()
        wallet_view.toggle_airplane_mode()
        wallet_view.accounts_status_account.click_until_presence_of_element(wallet_view.send_transaction_button)
        send_transaction = wallet_view.send_transaction_button.click()
        send_transaction.chose_recipient_button.click()
        send_transaction.accounts_button.click()
        send_transaction.element_by_text("Status account").click()
        send_transaction.amount_edit_box.click()
        send_transaction.amount_edit_box.set_value("0")
        send_transaction.confirm()
        send_transaction.sign_transaction_button.click()
        if send_transaction.sign_with_password.is_element_displayed():
            self.driver.fail("Sign transaction button is active in offline mode")

    @marks.testrail_id(6225)
    @marks.medium
    def test_send_funds_between_accounts_in_multiaccount_instance(self):
        sign_in_view = SignInView(self.driver)
        sign_in_view.create_user()
        wallet_view = sign_in_view.wallet_button.click()
        wallet_view.set_up_wallet()
        status_account_address = wallet_view.get_wallet_address()[2:]
        wallet_view.back_button.click()
        self.network_api.get_donate(status_account_address)
        wallet_view.wait_balance_is_changed()
        account_name = 'subaccount'
        wallet_view.add_account(account_name)

        wallet_view.just_fyi("Send transaction to new account")
        wallet_view.accounts_status_account.click()
        send_transaction = wallet_view.send_transaction_button.click()
        send_transaction.amount_edit_box.click()
        transaction_amount = send_transaction.get_unique_amount()
        send_transaction.amount_edit_box.set_value(transaction_amount)
        send_transaction.confirm()
        send_transaction.chose_recipient_button.click()
        send_transaction.accounts_button.click()
        send_transaction.element_by_text(account_name).click()
        send_transaction.sign_transaction_button.click()
        send_transaction.sign_transaction()
        self.network_api.wait_for_confirmation_of_transaction(status_account_address, transaction_amount)
        self.network_api.verify_balance_is_updated('0.1', status_account_address)

        wallet_view.just_fyi("Verifying previously sent transaction in new account")
        wallet_view.back_button.click()
        wallet_view.get_account_by_name(account_name).click()
        wallet_view.send_transaction_button.click()
        wallet_view.back_button.click()
        balance_after_receiving_tx = float(wallet_view.get_asset_amount_by_name('ETHro'))
        expected_balance = self.network_api.get_rounded_balance(balance_after_receiving_tx, transaction_amount)
        if balance_after_receiving_tx != expected_balance:
            self.driver.fail('New account balance %s does not match expected %s after receiving a transaction' % (
                balance_after_receiving_tx, transaction_amount))

        wallet_view.just_fyi("Sending eth from new account to main account")
        updated_balance = self.network_api.get_balance(status_account_address)
        wallet_view.send_transaction_button.click()
        send_transaction.amount_edit_box.click()
        transaction_amount_1 = round(float(transaction_amount) * 0.05, 11)
        send_transaction.amount_edit_box.set_value(str(transaction_amount_1))
        send_transaction.confirm()
        send_transaction.chose_recipient_button.click()
        send_transaction.accounts_button.click()
        send_transaction.element_by_text('Status account').click()
        send_transaction.sign_transaction_button.click()
        send_transaction.sign_transaction()
        send_transaction.back_button.click()
        sub_account_address = wallet_view.get_wallet_address(account_name)[2:]
        self.network_api.wait_for_confirmation_of_transaction(status_account_address, transaction_amount)
        self.network_api.verify_balance_is_updated(updated_balance, status_account_address)
        transactions_view = wallet_view.transaction_history_button.click()

        wallet_view.just_fyi("Check transactions on subaccount")
        transactions_view.transactions_table.find_transaction(amount=transaction_amount)
        transactions_view.transactions_table.find_transaction(amount=format(float(transaction_amount_1),'.11f').rstrip('0'))
        self.network_api.verify_balance_is_updated(updated_balance, status_account_address)

        wallet_view.just_fyi("Verify total ETH on main wallet view")
        self.network_api.wait_for_confirmation_of_transaction(status_account_address, transaction_amount_1, 3)
        self.network_api.verify_balance_is_updated((updated_balance + transaction_amount_1), status_account_address)
        send_transaction.back_button.click()
        balance_of_sub_account = float(self.network_api.get_balance(sub_account_address)) / 1000000000000000000
        balance_of_status_account = float(self.network_api.get_balance(status_account_address)) / 1000000000000000000
        total_eth_from_two_accounts = float(wallet_view.get_asset_amount_by_name('ETHro'))
        expected_balance = self.network_api.get_rounded_balance(total_eth_from_two_accounts,
                                                                (balance_of_status_account + balance_of_sub_account))

        if total_eth_from_two_accounts != expected_balance:
            self.driver.fail('Total wallet balance %s != of Status account (%s) + SubAccount (%s)' % (
                total_eth_from_two_accounts, balance_of_status_account, balance_of_sub_account))

    @marks.testrail_id(6235)
    @marks.medium
    def test_can_change_account_settings(self):
        sign_in_view = SignInView(self.driver)
        sign_in_view.create_user()
        wallet_view = sign_in_view.wallet_button.click()
        wallet_view.set_up_wallet()
        status_account_address = wallet_view.get_wallet_address()
        wallet_view.get_account_options_by_name().click()

        wallet_view.just_fyi('open Account Settings screen and check that all elements are shown')
        wallet_view.account_settings_button.click()
        for text in 'On Status tree', status_account_address, "m/44'/60'/0'/0/0":
            if not wallet_view.element_by_text(text).is_element_displayed():
                self.errors.append("'%s' text is not shown on Account Settings screen!" % text)

        wallet_view.just_fyi('change account name/color and verified applied changes')
        account_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        wallet_view.account_name_input.send_keys(account_name)
        wallet_view.account_color_button.select_color_by_position(1)
        wallet_view.apply_settings_button.click()
        wallet_view.element_by_text('This device').scroll_to_element()
        wallet_view.back_button.click()
        wallet_view.back_button.click()
        account_button = wallet_view.get_account_by_name(account_name)
        if not account_button.is_element_displayed():
            self.driver.fail('Account name was not changed')
        if not account_button.color_matches('multi_account_color.png'):
            self.driver.fail('Account color does not match expected')

        self.errors.verify_no_errors()

    @marks.testrail_id(6282)
    @marks.medium
    def test_can_scan_eip_681_links(self):
        sign_in_view = SignInView(self.driver)
        sign_in_view.recover_access(transaction_senders['C']['passphrase'])
        wallet_view = sign_in_view.wallet_button.click()
        wallet_view.set_up_wallet()
        send_transaction_view = SendTransactionView(self.driver)
        url_data = {
            'ens_for_receiver': {
                'url': 'ethereum:0xc55cf4b03948d7ebc8b9e8bad92643703811d162@3/transfer?address=nastya.stateofus.eth&uint256=1e-1',
                'data':{
                    'asset': 'STT',
                    'amount': '0.1',
                    'address': '0x58d8…F2ff',
                },
            },
            'gas_settings': {
                'url': 'ethereum:0x3d597789ea16054a084ac84ce87f50df9198f415@3?value=1e16&gasPrice=1000000000&gasLimit=100000',
                'data': {
                    'amount': '0.01',
                    'asset': 'ETHro',
                    'address': '0x3D59…F415',
                    'gas_limit': '100000',
                    'gas_price': '1',
                },
            },
            'payment_link': {
                'url': 'ethereum:pay-0xc55cf4b03948d7ebc8b9e8bad92643703811d162@3/transfer?address=0x3d597789ea16054a084ac84ce87f50df9198f415&uint256=1e1',
                'data': {
                    'amount': '10',
                    'asset': 'STT',
                    'address': '0x3D59…F415',
                },
            },
            'validation_amount_too_presize': {
                'url': 'ethereum:0xc55cf4b03948d7ebc8b9e8bad92643703811d162@3/transfer?address=0x101848D5C5bBca18E6b4431eEdF6B95E9ADF82FA&uint256=1e-19',
                'data': {
                    'amount': '1e-19',
                    'asset': 'STT',
                    'address': '0x1018…82FA',

                },
                'send_transaction_validation_error': 'Amount is too precise',
            },
            'validation_amount_too_big': {
                'url': 'ethereum:0x101848D5C5bBca18E6b4431eEdF6B95E9ADF82FA@3?value=1e25',
                'data': {
                    'amount': '10000000',
                    'asset': 'ETHro',
                    'address': '0x1018…82FA',

                },
                'send_transaction_validation_error': 'Insufficient funds',
            },
            'validation_wrong_chain_id': {
                'url': 'ethereum:0x101848D5C5bBca18E6b4431eEdF6B95E9ADF82FA?value=1e17',
                'error': 'Network does not match',
                'data': {
                    'amount': '0.1',
                    'asset': 'ETHro',
                    'address': '0x1018…82FA',
                },
            },
            'validation_wrong_address': {
                'url': 'ethereum:0x744d70fdbe2ba4cf95131626614a1763df805b9e@3/transfer?address=blablabla&uint256=1e10',
                'error': 'Invalid address',
            },
        }

        for key in url_data:
            wallet_view.just_fyi('Checking %s case' % key)
            wallet_view.scan_qr_button.click()
            if wallet_view.allow_button.is_element_displayed():
                wallet_view.allow_button.click()
            wallet_view.enter_qr_edit_box.set_value(url_data[key]['url'])
            wallet_view.ok_button.click()
            if url_data[key].get('error'):
                if not wallet_view.element_by_text_part(url_data[key]['error']).is_element_displayed():
                    self.errors.append('Expected error %s is not shown' % url_data[key]['error'])
                wallet_view.ok_button.click()
            if url_data[key].get('data'):
                if 'gas' in key:
                    actual_data = send_transaction_view.get_values_from_send_transaction_bottom_sheet(gas=True)
                else:
                    actual_data = send_transaction_view.get_values_from_send_transaction_bottom_sheet()
                difference_in_data = url_data[key]['data'].items() - actual_data.items()
                if difference_in_data:
                    self.errors.append(
                        'In %s case returned value does not match expected in %s' % (key, repr(difference_in_data)))
                if url_data[key].get('send_transaction_validation_error'):
                    error = url_data[key]['send_transaction_validation_error']
                    if not wallet_view.element_by_text_part(error).is_element_displayed():
                        self.errors.append(
                            'Expected error %s is not shown' % error)
                send_transaction_view.cancel_button.click()

        self.errors.verify_no_errors()
