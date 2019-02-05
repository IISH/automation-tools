class Error:
    def __init__(self):
        pass

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
    INVALID_FILENAME_MSG = "Found file with name '{}', but expected format {}"
    NO_PRESERVATION_FILE = 7
    NO_PRESERVATION_FILE_MSG = "Found file with name '{}' which does not have a preservation file"
    SEQUENCE_NOT_UNIQUE = 8
    SEQUENCE_NOT_UNIQUE_MSG = "Sequence is used before '{}'"
    SEQUENCE_DOES_NOT_START_WITH_1 = 9
    SEQUENCE_DOES_NOT_START_WITH_1_MSG = "Sequences must start with the number 1"
    SEQUENCE_INTERVAL_NOT_1 = 10
    SEQUENCE_INTERVAL_NOT_1_MSG = "Sequences should start from 1 and increment by 1. Expect {} but got {}"
    UNSUPPORTED_TYPE = 11
    UNSUPPORTED_TYPE_MSG = "Unsupported package type '{}'. Expect archival (dot) or scanned on demand (no dot)."
