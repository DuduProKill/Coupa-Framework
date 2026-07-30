"""Gerenciador de contexto compartilhado do Playwright.

Elimina a duplicacao de abertura de contextos do Playwright que existia em:
- coupa_scraper.py (contexto para extracao)
- download_scraper.py (contexto para download)
- pdf_generator.py (contexto para geracao de PDF)

Cada um consumia ~200-400MB de RAM. Agora o pool gerencia e reusa contextos.
"""

import asyncio
import os
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from modules.config import resolve_edge_executable


class PlaywrightPool:
    """Pool singleton de contextos do Playwright para Microsoft Edge.

    Uso:
        async with PlaywrightPool.get_context(user_data_dir="...") as context:
            page = context.pages[0] or await context.new_page()
    """

    _instance: Optional["PlaywrightPool"] = None
    _lock = threading.Lock()
    _async_lock: Optional[asyncio.Lock] = None

    def __init__(self):
        self._playwright = None
        self._contexts: Dict[str, Any] = {}
        # amazonq-ignore-next-line
        self._ref_count: Dict[str, int] = {}

    @classmethod
    def get_instance(cls) -> "PlaywrightPool":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    async def _start_playwright(self):
        """Inicializa o Playwright uma unica vez."""
        if self._playwright is None:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()

    async def get_context(self, user_data_dir: str, channel: str = "msedge",
                          headless: bool = False, **kwargs) -> Any:
        """Retorna um contexto persistente do Edge, reutilizando se possivel."""
        if PlaywrightPool._async_lock is None:
            PlaywrightPool._async_lock = asyncio.Lock()

        async with PlaywrightPool._async_lock:
            caminho_edge = resolve_edge_executable()
            context_key = user_data_dir

            if context_key in self._contexts:
                # amazonq-ignore-next-line
                self._ref_count[context_key] += 1
                return self._contexts[context_key]

            await self._start_playwright()
            context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                executable_path=caminho_edge,
                channel=channel,
                headless=headless,
                no_viewport=True,
                **kwargs
            )

            self._contexts[context_key] = context
            self._ref_count[context_key] = 1
            return context

    async def release_context(self, user_data_dir: str):
        """Libera um contexto quando nao for mais necessario.

        So fecha efetivamente quando o contagem de referencias chegar a zero.
        """
        context_key = user_data_dir
        if context_key not in self._contexts:
            return

        self._ref_count[context_key] -= 1
        if self._ref_count[context_key] <= 0:
            try:
                await self._contexts[context_key].close()
            except Exception:
                pass
            del self._contexts[context_key]
            del self._ref_count[context_key]

    async def cleanup_all(self):
        """Fecha todos os contextos e o Playwright."""
        for key in list(self._contexts.keys()):
            try:
                await self._contexts[key].close()
            except Exception:
                pass
        self._contexts.clear()
        self._ref_count.clear()
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None


class PlaywrightContextManager:
    """Context manager para uso com 'async with'.

    Uso:
        async with PlaywrightContextManager(user_data_dir="...") as context:
            page = context.pages[0] or await context.new_page()
    """

    def __init__(self, user_data_dir: str, channel: str = "msedge",
                 headless: bool = False, **kwargs):
        self.user_data_dir = user_data_dir
        self.channel = channel
        self.headless = headless
        self.kwargs = kwargs
        self._context = None

    async def __aenter__(self):
        pool = PlaywrightPool.get_instance()
        self._context = await pool.get_context(
            user_data_dir=self.user_data_dir,
            channel=self.channel,
            headless=self.headless,
            **self.kwargs
        )
        return self._context

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pool = PlaywrightPool.get_instance()
        await pool.release_context(self.user_data_dir)

