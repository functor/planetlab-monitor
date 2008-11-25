import turbogears as tg
from turbogears import controllers, expose, flash
# from monitorweb import model
# import logging
# log = logging.getLogger("monitorweb.controllers")

class Root(controllers.RootController):
    @expose(template="monitorweb.templates.welcome")
    def index(self):
        import time
        # log.debug("Happy TurboGears Controller Responding For Duty")
        flash("Your application is now running")
        return dict(now=time.ctime())
