class Error:
    NO_MANIFEST = 1
    NO_MANIFEST_MSG = "Expecting a manifest at {}"
    NO_GROUPS = 2
    NO_GROUPS_MSG = "Found no file groups in the fileset {}"
    UNKNOWN_GROUPS = 3
    UNKNOWN_GROUPS_MSG = "Found folder {} which is not of one of type {}"
