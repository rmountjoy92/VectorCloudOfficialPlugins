import json
from datetime import datetime
from flask import render_template
from flask_socketio import emit
from vectorcloud import db, socketio
from vectorcloud.main.models import Vectors, PluginStorage
from vectorcloud.main.moment import create_moment
from vectorcloud.main.utils import run_plugin


class Plugin:
    def __init__(self, *args, **kwargs):

        # parse user supplied plugin settings
        for key, value in kwargs.items():
            self.__dict__[key] = value

        # set defaults for omitted options
        if not hasattr(self, "name"):
            self.name = "Unnamed logbook item"
        if not hasattr(self, "vector_id"):
            self.vector_id = 1
        if not hasattr(self, "info"):
            self.info = None
        if not hasattr(self, "log_type"):
            self.log_type = None
        if not hasattr(self, "emit_only"):
            self.emit_only = False
        if not hasattr(self, "from_item"):
            self.from_item = 0

    def interface_data(self):
        interface_data = {
            "plugin_settings": [
                {
                    "name": "name",
                    "default": "Unnamed logbook item",
                    "description": "title of the newly created log item",
                },
                {
                    "name": "vector_id",
                    "default": "first entry",
                    "description": "associate a vector to the log item",
                },
                {
                    "name": "info",
                    "default": "None",
                    "description": "optionally include description text for the log item",
                },
                {
                    "name": "emit_only",
                    "default": "False",
                    "description": "when true, no log item is created, but the logbook is still refreshed in the web client",
                },
            ],
            "plugin_description": "Create a logbook item and update the UI, optionally just update the UI",
            "plugin_icons": [
                {
                    "mdi_class": "timeline",
                    "class": "show-logbook-btn",
                    "tooltip": "Logbook",
                }
            ],
            "plugin_panels": [
                {"class": "logbook-panel", "template": "logbook-panel.html"},
            ],
            "plugin_extra_html": ["logbook-rows.html"],
            "plugin_js": ["logbook.js"],
        }
        return interface_data

    def get_html(self, vector):
        logbook_items = (
            PluginStorage.query.filter_by(
                entry_type="logbook_item", vector_id=vector.id
            )
            .order_by(PluginStorage.id.desc())
            .all()
        )

        if self.from_item < 0:
            self.from_item = 0
        elif self.from_item > len(logbook_items):
            self.from_item = len(logbook_items) - 30

        items = logbook_items[self.from_item : self.from_item + 30]
        for item in items:
            value_json = json.loads(item.value_json)
            item.dt = value_json["dt"]
            item = create_moment(item)
            item.value_json_x = value_json

        html = render_template(
            "plugins/logbook-rows.html", logbook_items=items, from_item=self.from_item
        )
        return html

    def on_startup(self):
        @socketio.on("request_logbook")
        def handle_logbook_request(json={}):
            run_plugin(
                "logbook", {"emit_only": True, "from_item": json.get("from_item", 0)}
            )

        @socketio.on("logbook_log")
        def handle_logbook_log(json):
            run_plugin(
                "logbook",
                {
                    "name": json.get("name", None),
                    "info": json.get("info", None),
                    "log_type": json.get("log_type", None),
                },
            )

        @socketio.on("logbook_clear")
        def handle_logbook_clear(json):
            PluginStorage.query.filter_by(
                entry_type="logbook_item", vector_id=json.get("vector_id")
            ).delete()
            db.session.commit()

    def run(self):
        if self.emit_only is False:
            log = PluginStorage()
            log.plugin = "logbook"
            log.entry_type = "logbook_item"
            log.vector_id = self.vector_id
            log.value_json = json.dumps(
                {
                    "name": self.name,
                    "info": self.info,
                    "dt": str(datetime.now()),
                    "log_type": self.log_type,
                    "vector_id": self.vector_id,
                }
            )
            db.session.add(log)
            db.session.commit()

        html_dict = {}
        for vector in Vectors.query.all():
            html_dict[vector.id] = self.get_html(vector)

        emit("logbook", html_dict, broadcast=True, namespace="/")
        return "ok"
