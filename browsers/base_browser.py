from playwright.async_api import Page, ElementHandle, TimeoutError as PlaywrightTimeoutError
from config.settings import ACTION_TIMEOUT
import logging
import asyncio
from typing import List, Dict, Any, Optional, Union, Callable
import json
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class BaseBrowserActions:
    def __init__(self, page: Page):
        self.page = page
        
    async def navigate(self, url: str) -> None:
        """Navigate to a URL"""
        logger.info(f"Navigating to {url}")
        try:
            response = await self.page.goto(url, wait_until="networkidle")
            if not response or response.status >= 400:
                logger.error(f"Failed to navigate to {url}. Status: {response.status if response else 'None'}")
                raise Exception(f"Failed to navigate to {url}")
            logger.info(f"Successfully navigated to {url}")
        except PlaywrightTimeoutError:
            logger.warning(f"Navigation timeout for {url}, continuing anyway")
    
    async def wait_for_selector(self, selector: str, timeout: int = ACTION_TIMEOUT) -> Optional[ElementHandle]:
        """Wait for an element to be present on the page"""
        try:
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            return element
        except PlaywrightTimeoutError:
            logger.warning(f"Timeout waiting for selector: {selector}")
            return None
    
    async def fill_input(self, selector: str, value: str) -> bool:
        """Fill an input field with a value"""
        try:
            element = await self.wait_for_selector(selector)
            if not element:
                return False
            
            await element.fill(value)
            return True
        except Exception as e:
            logger.error(f"Error filling input {selector}: {str(e)}")
            return False
    
    async def click(self, selector: str, timeout: int = ACTION_TIMEOUT) -> bool:
        """Click on an element"""
        try:
            element = await self.wait_for_selector(selector, timeout)
            if not element:
                return False
            
            await element.click()
            return True
        except Exception as e:
            logger.error(f"Error clicking {selector}: {str(e)}")
            return False
    
    async def select_option(self, selector: str, value: str) -> bool:
        """Select an option from a dropdown"""
        try:
            element = await self.wait_for_selector(selector)
            if not element:
                return False
            
            await self.page.select_option(selector, value=value)
            return True
        except Exception as e:
            logger.error(f"Error selecting option {value} for {selector}: {str(e)}")
            return False
    
    async def get_text(self, selector: str) -> Optional[str]:
        """Get text content of an element"""
        try:
            element = await self.wait_for_selector(selector)
            if not element:
                return None
            
            return await element.text_content()
        except Exception as e:
            logger.error(f"Error getting text for {selector}: {str(e)}")
            return None
    
    async def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """Get attribute value of an element"""
        try:
            element = await self.wait_for_selector(selector)
            if not element:
                return None
            
            return await element.get_attribute(attribute)
        except Exception as e:
            logger.error(f"Error getting attribute {attribute} for {selector}: {str(e)}")
            return None
    
    async def wait_for_navigation(self, timeout: int = ACTION_TIMEOUT) -> bool:
        """Wait for navigation to complete"""
        try:
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            logger.warning("Navigation timeout, continuing anyway")
            return False
    
    async def get_page_html(self) -> str:
        """Get the HTML content of the current page"""
        return await self.page.content()
    
    async def eval_on_page(self, script: str) -> Any:
        """Evaluate JavaScript on the page"""
        return await self.page.evaluate(script)
    
    async def wait_for_response(self, url_pattern: str, timeout: int = ACTION_TIMEOUT) -> Optional[Dict[str, Any]]:
        """Wait for a specific API response based on URL pattern"""
        response_data = None
        
        def handle_response(response):
            nonlocal response_data
            if re.search(url_pattern, response.url):
                response_data = response
                return True
            return False
        
        try:
            await self.page.wait_for_response(handle_response, timeout=timeout)
            if response_data:
                try:
                    return json.loads(await response_data.text())
                except json.JSONDecodeError:
                    return {"raw_text": await response_data.text()}
            return None
        except PlaywrightTimeoutError:
            logger.warning(f"Timeout waiting for response matching: {url_pattern}")
            return None
    
    async def extract_data_with_selectors(self, selectors_map: Dict[str, str]) -> Dict[str, Optional[str]]:
        """Extract data using a map of field names to selectors"""
        result = {}
        for field, selector in selectors_map.items():
            result[field] = await self.get_text(selector)
        return result
    
    async def parse_current_page(self, parser_fn: Callable[[str], Dict[str, Any]]) -> Dict[str, Any]:
        """Parse the current page HTML using a custom parser function"""
        html = await self.get_page_html()
        return parser_fn(html)
    
    async def extract_with_bs4(self, css_selector: str) -> List[Dict[str, str]]:
        """Extract data using BeautifulSoup"""
        html = await self.get_page_html()
        soup = BeautifulSoup(html, 'html.parser')
        elements = soup.select(css_selector)
        
        results = []
        for el in elements:
            attrs = {k: v for k, v in el.attrs.items()}
            attrs['text'] = el.get_text(strip=True)
            results.append(attrs)
        
        return results
    
    async def handle_dialog(self, accept: bool = True, text: str = "") -> None:
        """Set up dialog handler for alerts, confirms, prompts"""
        async def dialog_handler(dialog):
            logger.info(f"Dialog appeared: {dialog.message}")
            if accept:
                if text and dialog.type == "prompt":
                    await dialog.accept(text)
                else:
                    await dialog.accept()
            else:
                await dialog.dismiss()
        
        self.page.on("dialog", dialog_handler)
    
    async def screenshot(self, path: str) -> str:
        """Take a screenshot of the current page"""
        await self.page.screenshot(path=path)
        return path
    
    async def retry_action(self, action_fn, max_retries: int = 3, retry_delay: float = 1.0):
        """Retry an action with exponential backoff"""
        retries = 0
        while retries < max_retries:
            try:
                return await action_fn()
            except Exception as e:
                retries += 1
                if retries >= max_retries:
                    raise e
                delay = retry_delay * (2 ** (retries - 1))
                logger.warning(f"Action failed, retrying in {delay:.1f}s ({retries}/{max_retries})")
                await asyncio.sleep(delay)
