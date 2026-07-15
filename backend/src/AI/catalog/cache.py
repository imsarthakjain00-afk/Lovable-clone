import json
import os
import logging
from typing import Dict
from src.AI.catalog.schemas import DesignCatalogCache, DesignMetadata

logger = logging.getLogger(__name__)
CACHE_FILE = os.path.join(os.path.dirname(__file__), "catalog_cache.json")

class DesignCache:
    _cache: DesignCatalogCache = None

    @classmethod
    def load(cls) -> DesignCatalogCache:
        if cls._cache:
            return cls._cache

        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cls._cache = DesignCatalogCache(**data)
                    logger.info(f"Loaded design catalog cache with {len(cls._cache.designs)} designs.")
                    return cls._cache
            except Exception as e:
                logger.warning(f"Failed to load design cache: {e}. Rebuilding...")

        cls._cache = DesignCatalogCache()
        return cls._cache

    @classmethod
    def save(cls, cache: DesignCatalogCache):
        cls._cache = cache
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                f.write(cache.model_dump_json(indent=2))
        except Exception as e:
            logger.error(f"Failed to save design cache: {e}")
