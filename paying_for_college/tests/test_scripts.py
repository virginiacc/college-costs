import unittest
import django
import json

import mock
from paying_for_college.disclosures.scripts import api_utils, update_colleges
from paying_for_college.disclosures.scripts import nat_stats

YEAR = api_utils.LATEST_YEAR
MOCK_YAML = """\
completion_rate:\n\
  min: 0\n\
  max: 1\n\
  median: 0.4379\n\
  average_range: [.3180, .5236]\n
"""


class TestUpdater(django.test.TestCase):

    fixtures = ['test_fixture.json']

    mock_dict = {'results':
                 [{'id': 155317,
                   'ope6_id': 5555,
                   'ope8_id': 55500,
                   'enrollment': 10000,
                   'accreditor': "Santa",
                   'url': '',
                   'degrees_predominant': '',
                   'degrees_highest': '',
                   'ownership': '',
                   'main_campus': True,
                   'online_only': False,
                   'operating': True,
                   'under_investigation': False,
                   'RETENTRATE': '',
                   'RETENTRATELT4': '',  # NEW
                   'REPAY3YR': '',  # NEW
                   'DEFAULTRATE': '',
                   'AVGSTULOANDEBT': '',
                   'MEDIANDEBTCOMPLETER': '',  # NEW
                   'city': 'Lawrence'}],
                 'metadata': {'page': 0}
                 }

    @mock.patch('paying_for_college.disclosures.scripts.update_colleges.requests.get')
    def test_update_colleges(self, mock_requests):
        mock_response = mock.Mock()
        mock_response.json.return_value = self.mock_dict
        mock_response.ok = True
        mock_requests.return_value = mock_response
        (FAILED, NO_DATA, endmsg) = update_colleges.update()
        self.assertTrue(len(NO_DATA) == 0)
        self.assertTrue(len(FAILED) == 0)
        self.assertTrue('updated' in endmsg)

    @mock.patch('paying_for_college.disclosures.scripts.update_colleges.requests.get')
    def test_update_colleges_not_OK(self, mock_requests):
        mock_response = mock.Mock()
        mock_response.ok = False
        mock_response.reason = "Testing OK == False"
        (FAILED, NO_DATA, endmsg) = update_colleges.update()
        # print("\n after OK == False, FAILED is %s" % FAILED)
        self.assertTrue(len(FAILED) == 2)
        mock_requests.status_code = 429
        (FAILED, NO_DATA, endmsg) = update_colleges.update()
        # print("after 429 FAILED is %s" % FAILED)
        self.assertTrue(len(FAILED) == 2)

    @mock.patch('paying_for_college.disclosures.scripts.update_colleges.requests.get')
    def test_update_colleges_bad_responses(self, mock_requests):
        mock_response = mock.Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'results': []}
        (FAILED, NO_DATA, endmsg) = update_colleges.update()
        # print("after results==[], NO_DATA is %s" % FAILED)
        self.assertTrue('no data' in endmsg)


class TestScripts(unittest.TestCase):

    mock_dict = {'results':
                 [{'id': 123456,
                   'key': 'value'}],
                 'metadata': {'page': 0}
                 }

    def test_calculate_percent(self):
        percent = api_utils.calculate_group_percent(100, 900)
        self.assertTrue(percent == 10.0)
        percent = api_utils.calculate_group_percent(0, 0)
        self.assertTrue(percent == 0)

    @mock.patch('paying_for_college.disclosures.scripts.api_utils.requests.get')
    def test_get_repayment_data(self, mock_requests):
        mock_response = mock.Mock()
        expected_dict = {'results':
                         [{'2013.repayment.5_yr_repayment.completers': 100,
                          '2013.repayment.5_yr_repayment.noncompleters': 900}]}
        mock_response.json.return_value = expected_dict
        mock_requests.return_value = mock_response
        data = api_utils.get_repayment_data(123456, YEAR)
        self.assertTrue(data['completer_repayment_rate_after_5_yrs'] == 10.0)

    @mock.patch('paying_for_college.disclosures.scripts.api_utils.requests.get')
    def test_export_spreadsheet_no_data(self, mock_requests):
        mock_response = mock.Mock()
        expected_dict = {}
        mock_response.json.return_value = expected_dict
        mock_requests.return_value = mock_response
        data = api_utils.export_spreadsheet(YEAR)
        self.assertTrue(data == expected_dict)

    @mock.patch('paying_for_college.disclosures.scripts.api_utils.requests.get')
    def test_search_by_school_name(self, mock_requests):
        mock_response = mock.Mock()
        mock_response.json.return_value = self.mock_dict
        mock_requests.return_value = mock_response
        data = api_utils.search_by_school_name('mockname')
        self.assertTrue(data == self.mock_dict['results'])

    @mock.patch('paying_for_college.disclosures.scripts.api_utils.requests.get')
    def test_export_spreadsheet(self, mock_requests):
        mock_response = mock.Mock()
        mock_response.text = json.dumps({'results': []})
        mock_response.json.return_value = self.mock_dict
        mock_requests.return_value = mock_response
        data = api_utils.export_spreadsheet(YEAR)
        self.assertTrue(data == self.mock_dict)

    def test_build_field_string(self):
        fstring = api_utils.build_field_string(YEAR)
        self.assertTrue(fstring.startswith('id'))
        self.assertTrue(fstring.endswith('25000'))

    @mock.patch('paying_for_college.disclosures.scripts.nat_stats.requests.get')
    def test_get_stats_yaml(self, mock_requests):
        mock_response = mock.Mock()
        mock_response.text = MOCK_YAML
        mock_response.ok = True
        mock_requests.return_value = mock_response
        data = nat_stats.get_stats_yaml()
        print "returned dict from yaml is {0}".format(data)
        self.assertTrue(mock_requests.call_count == 1)
        self.assertTrue(data['completion_rate']['max'] == 1)
        mock_response.ok = False
        mock_requests.return_value = mock_response
        data = nat_stats.get_stats_yaml()
        self.assertTrue(mock_requests.call_count == 2)
        self.assertTrue(data == {})

    @mock.patch('paying_for_college.disclosures.scripts.nat_stats.update_national_stats_file')
    def test_get_national_stats(self, mock_update):
        mock_update.return_value = 'OK'
        data = nat_stats.get_national_stats()
        self.assertTrue(mock_update.call_count == 0)
        self.assertTrue(data['completion_rate']['max'] == 1)
        data2 = nat_stats.get_national_stats(update=True)
        self.assertTrue(mock_update.call_count == 1)
        self.assertTrue(data2['completion_rate']['max'] == 1)

    def test_get_prepped_stats(self):
        stats = nat_stats.get_prepped_stats()
        self.assertTrue(stats['completionRateMedian'] <= 1)
