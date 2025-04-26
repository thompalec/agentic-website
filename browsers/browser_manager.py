from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from config.settings import HEADLESS, SLOW_MO, NAVIGATION_TIMEOUT
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrowserManager:
    _instance = None
    _playwright = None
    _browser = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserManager, cls).__new__(cls)
        return cls._instance
    
    async def initialize(self):
        if self._playwright is None:
            logger.info("Initializing playwright browser")
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=HEADLESS,
                slow_mo=SLOW_MO
            )
            logger.info(f"Browser initialized (headless: {HEADLESS})")
    
    async def shutdown(self):
        if self._browser:
            logger.info("Closing browser")
            await self._browser.close()
            self._browser = None
        
        if self._playwright:
            logger.info("Stopping playwright")
            await self._playwright.stop()
            self._playwright = None
    
    @asynccontextmanager
    async def create_context(self) -> AsyncGenerator[BrowserContext, None]:
        await self.initialize()
        
        context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        
        try:
            yield context
        finally:
            await context.close()
    
    @asynccontextmanager
    async def create_page(self) -> AsyncGenerator[Page, None]:
        async with self.create_context() as context:
            page = await context.new_page()
            page.set_default_timeout(NAVIGATION_TIMEOUT)
            
            try:
                yield page
            finally:
                await page.close()
