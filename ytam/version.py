import pkg_resources

try:
    version = pkg_resources.require("ytam")[0].version
except pkg_resources.DistributionNotFound:
    version = "dev"
