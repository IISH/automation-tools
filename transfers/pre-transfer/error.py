class Error:
    NO_MANIFEST = 1
    NO_MANIFEST_MSG = "Expecting a manifest at '{}'"
    NO_GROUPS = 2
    NO_GROUPS_MSG = "Found no file groups in the fileset '{}'"
    UNKNOWN_GROUPS = 3
    UNKNOWN_GROUPS_MSG = "Found folder name '{}' which is not of one of type {}"
    NO_HEADER = 4
    NO_HEADER_MSG = "No CSV header found in '{}'"
    MISSING_HEADER_ITEM_FOR_EXISTING_FOLDER = 5
    NO_HEADER_ITEM_MSG = "Existing folder '{}' not declared in CSV header {}"
    MISSING_FOLDER_NAME_FOR_EXISTING_HEADER = 6
    MISSING_FOLDER_NAME_FOR_EXISTING_HEADER_MSG = "Existing header '{}' not found on folder '{}'"
    UNKNOWN_HEADER = 7
    UNKNOWN_HEADER_MSG = "CSV header '{}' is not of type '{}'"
    DUPLICATE_HEADER = 8
    DUPLICATE_HEADER_MSG = "Key should be unique but found {} identical keys in for CSV header '{}'"