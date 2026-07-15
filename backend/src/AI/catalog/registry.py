import logging
from typing import List, Optional
from src.AI.catalog.schemas import DesignMetadata, DesignCatalogCache
from src.AI.catalog.loader import CatalogLoader
from src.AI.catalog.cache import DesignCache

logger = logging.getLogger(__name__)

class DesignRegistry:
    _is_loaded: bool = False

    @classmethod
    def load(cls):
        """
        Loads metadata from cache or rescans if empty.
        """
        if cls._is_loaded:
            return

        cache = DesignCache.load()
        
        # If cache is empty, run discovery
        if not cache.designs:
            logger.info("Design cache empty, running discovery...")
            designs = CatalogLoader.discover_all()
            for d in designs:
                cache.designs[d.id] = d
            DesignCache.save(cache)
            
        cls._is_loaded = True

    @classmethod
    def get_all(cls) -> List[DesignMetadata]:
        cls.load()
        cache = DesignCache.load()
        return list(cache.designs.values())

    @classmethod
    def get_by_id(cls, design_id: str) -> Optional[DesignMetadata]:
        cls.load()
        cache = DesignCache.load()
        return cache.designs.get(design_id)
        
    @classmethod
    def reload(cls):
        """Forces a rescan (useful after git pull)."""
        logger.info("Forcing registry reload...")
        cache = DesignCatalogCache()
        designs = CatalogLoader.discover_all()
        for d in designs:
            cache.designs[d.id] = d
        DesignCache.save(cache)
        cls._is_loaded = True
