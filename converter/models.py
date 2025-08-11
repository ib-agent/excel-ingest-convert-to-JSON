from django.db import models

# Legacy: provide a module-level cache to mirror Django views behavior.
# FastAPI download endpoint reads from this when storage service is not used.
processed_data_cache = {}
