'''
test command tests
'''
import mock
import unittest

from cirrus.test import nose_run
from cirrus.test import tox_run


class TestTest(unittest.TestCase):

    def setUp(self):
        self.home_patcher = mock.patch('cirrus.test.repo_directory')
        self.mock_repo_dir = self.home_patcher.start()
        self.mock_repo_dir.return_value = 'CIRRUS_HOME'

    def tearDown(self):
        self.home_patcher.stop()

    def test_tox_test(self):
        """test mox based test call"""
        with mock.patch('cirrus.test.local') as mock_local:
            mock_opts = mock.Mock()
            mock_opts.suite = 'default'
            mock_opts.options = '-o OPTION'
            mock_config = mock.Mock()
            mock_config.venv_name = mock.Mock()
            mock_config.venv_name.return_value = "VENV"
            mock_config.test_suite = mock.Mock(return_value={})

            tox_run(mock_config, mock_opts)
            self.failUnless(mock_local.called)
            self.failUnless(mock_config.venv_name.called)
            command = mock_local.call_args[0][0]
            self.assertEqual(command, '. CIRRUS_HOME/VENV/bin/activate && tox -o OPTION')

    @mock.patch('cirrus.test.is_anaconda')
    def test_tox_test_conda(self, mock_ana):
        """test mox based test call"""
        mock_ana.return_value = True
        with mock.patch('cirrus.test.local') as mock_local:
            mock_opts = mock.Mock()
            mock_opts.suite = 'default'
            mock_opts.options = '-o OPTION'
            mock_config = mock.Mock()
            mock_config.venv_name = mock.Mock()
            mock_config.venv_name.return_value = "VENV"
            mock_config.test_suite = mock.Mock(return_value={})

            tox_run(mock_config, mock_opts)
            self.failUnless(mock_local.called)
            self.failUnless(mock_config.venv_name.called)
            command = mock_local.call_args[0][0]
            self.assertEqual(command, 'source CIRRUS_HOME/VENV/bin/activate CIRRUS_HOME/VENV && tox -o OPTION')

    def test_tox_test_with_ini(self):
        """test mox based test call"""
        with mock.patch('cirrus.test.local') as mock_local:
            mock_opts = mock.Mock()
            mock_opts.suite = 'default'
            mock_opts.options = None
            mock_config = mock.Mock()
            mock_config.venv_name = mock.Mock()
            mock_config.venv_name.return_value = "VENV"
            mock_config.test_suite = mock.Mock(
                return_value={
                    'tox_ini': "TOXINI",
                    'test_options': "--womp"
                })

            tox_run(mock_config, mock_opts)
            self.failUnless(mock_local.called)
            self.failUnless(mock_config.venv_name.called)
            command = mock_local.call_args[0][0]
            self.assertEqual(command, '. CIRRUS_HOME/VENV/bin/activate && tox -c TOXINI --womp')

    @mock.patch('cirrus.test.is_anaconda')
    def test_nose_test_conda(self, mock_ana):
        """test nose_test call"""
        mock_ana.return_value = True
        with mock.patch('cirrus.test.local') as mock_local:
            mock_opts = mock.Mock()
            mock_opts.suite = 'default'
            mock_opts.options = '-o OPTION'
            mock_config = mock.Mock()
            mock_config.venv_name = mock.Mock()
            mock_config.venv_name.return_value = "VENV"
            mock_config.test_where = mock.Mock()
            mock_config.test_where.return_value = "WHERE"
            mock_config.test_suite = mock.Mock(return_value={})

            nose_run(mock_config, mock_opts)
            self.failUnless(mock_local.called)
            self.failUnless(mock_config.venv_name.called)
            self.failUnless(mock_config.test_where.called)
            command = mock_local.call_args[0][0]
            self.assertEqual(command, 'source CIRRUS_HOME/VENV/bin/activate CIRRUS_HOME/VENV && nosetests -w WHERE -o OPTION')

    def test_nose_test(self):
        """test nose_test call"""
        with mock.patch('cirrus.test.local') as mock_local:
            mock_opts = mock.Mock()
            mock_opts.suite = 'default'
            mock_opts.options = '-o OPTION'
            mock_config = mock.Mock()
            mock_config.venv_name = mock.Mock()
            mock_config.venv_name.return_value = "VENV"
            mock_config.test_where = mock.Mock()
            mock_config.test_where.return_value = "WHERE"
            mock_config.test_suite = mock.Mock(return_value={})

            nose_run(mock_config, mock_opts)
            self.failUnless(mock_local.called)
            self.failUnless(mock_config.venv_name.called)
            self.failUnless(mock_config.test_where.called)
            command = mock_local.call_args[0][0]
            self.assertEqual(command, '. CIRRUS_HOME/VENV/bin/activate && nosetests -w WHERE -o OPTION')



    def test_nose_test_options(self):
        """test nose_test call"""
        with mock.patch('cirrus.test.local') as mock_local:
            mock_opts = mock.Mock()
            mock_opts.suite = 'default'
            mock_opts.options = None
            mock_config = mock.Mock()
            mock_config.venv_name = mock.Mock()
            mock_config.venv_name.return_value = "VENV"
            mock_config.test_where = mock.Mock()
            mock_config.test_where.return_value = "WHERE"
            mock_config.test_suite = mock.Mock(return_value={'test_options': '--womp'})

            nose_run(mock_config, mock_opts)
            self.failUnless(mock_local.called)
            self.failUnless(mock_config.venv_name.called)
            self.failUnless(mock_config.test_where.called)
            command = mock_local.call_args[0][0]
            self.assertEqual(command, '. CIRRUS_HOME/VENV/bin/activate && nosetests -w WHERE --womp')



if __name__ == "__main__":
    unittest.main()
