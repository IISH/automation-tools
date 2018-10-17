class Error:
    EMPTY_FOLDER = 1
    EMPTY_FOLDER_MSG = "Expecting content in folder '{}'"
    NO_GROUPS = 2
    NO_GROUPS_MSG = "Found no file groups in the fileset '{}'"
    UNKNOWN_GROUPS = 3
    UNKNOWN_GROUPS_MSG = "Found folder name '{}' which is not of one of type {}"
    PRESERVATION_FOLDER_MISSING = 4
    PRESERVATION_FOLDER_MISSING_MSG = "The preservation folder is missing"
    MIXED_INV_NO = 5
    MIXED_INV_NO_MSG = "Found files without inventory numbers"
    INVALID_FILENAME = 6
    INVALID_FILENAME_MSG = "Found file with name '{}', but expected the name '{}' ending with a sequence number"
    NO_PRESERVATION_FILE = 7
    NO_PRESERVATION_FILE_MSG = "Found file with name '{}' which does not have a preservation file"