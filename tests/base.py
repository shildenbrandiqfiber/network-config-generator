"""
base classes for Flask test cases using the Flask-Testing module
"""
import os
import sys
import threading
import unittest
from flask_testing import TestCase
from selenium import webdriver
from werkzeug.serving import make_server
from app import app, db
from config import APP_BASE_DIR


class BaseFlaskTest(TestCase):

    def create_app(self):
        app.config.from_object('config.TestConfig')
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()


class BaseFlaskLiveServerTest(unittest.TestCase):
    """
    runs the application in a background thread (the LiveServerTestCase from Flask-Testing requires the "fork" start
    method of multiprocessing, which isn't the default on macOS and on Linux with Python 3.14+)
    """

    download_dir = os.path.join(APP_BASE_DIR, "tests", "_selenium", "downloads")

    def create_app(self):
        app.config.from_object('config.LiveServerTestConfig')
        return app

    def get_server_url(self):
        """
        Return the url of the test server, if no liveserver url is defined
        """
        url = None
        for arg in sys.argv:
            if 'liveserver' in arg:
                url = arg.split("=")[1]
        if url:
            return url
        return 'http://localhost:%s' % self.port

    def setUp(self):
        self.app = self.create_app()
        self.port = self.app.config["LIVESERVER_PORT"]
        self._app_context = self.app.app_context()
        self._app_context.push()
        db.create_all()

        self._server = make_server("localhost", self.port, self.app, threaded=True)
        self._server_thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._server_thread.start()

        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.manager.showWhenStarting", False)
        options.set_preference("browser.download.dir", self.download_dir)
        options.set_preference(
            "browser.helperApps.neverAsk.saveToDisk",
            "text/plain,text/csv,text/html,application/zip"
        )
        self.browser = webdriver.Firefox(options=options)
        self.browser.implicitly_wait(3)
        self.browser.set_window_size(1280, 1024)

    def tearDown(self):
        self.browser.quit()
        self._server.shutdown()
        self._server_thread.join()
        db.session.remove()
        db.drop_all()
        self._app_context.pop()
