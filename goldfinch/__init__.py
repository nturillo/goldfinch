# goldfinch/__init__.py

__app_name__ = 'goldfinch'
__version__ = '0.1.0'

( 
    SUCCESS,
    DIR_ERROR,
    FILE_ERROR,
    DB_ERROR,
    JSON_ERROR,
    GR_ERROR,
    DOWNLOAD_ERROR,
    NO_RESULTS
) = range(8)

ERRORS = {
    SUCCESS : "No errors",
    DIR_ERROR : "Directory error",
    FILE_ERROR : "File error",
    DB_ERROR : "Database error",
    JSON_ERROR : "JSON error",
    GR_ERROR : "Goodreads error",
    DOWNLOAD_ERROR : "Download error",
    NO_RESULTS : "no results found on libgen.is"
}