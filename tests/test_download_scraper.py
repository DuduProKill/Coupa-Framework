from modules.download_scraper import DownloadScraper


def test_analisar_arquivo_rejeita_de_acordo(tmp_path):
    """Arquivo cujo nome contém 'de acordo' deve ser rejeitado."""
    scraper = DownloadScraper(requisicoes=[], pasta_download=str(tmp_path))
    arquivo = tmp_path / 'de acordo.txt'
    arquivo.write_text('Orçamento conforme', encoding='utf-8')

    ok, result = scraper.analisar_arquivo(str(arquivo), '123', 'de acordo')

    assert ok is False
    assert result == 'nome'


def test_analisar_arquivo_sem_palavra_chave(tmp_path):
    """Arquivo sem palavra-chave no texto nem no nome deve ser rejeitado."""
    scraper = DownloadScraper(requisicoes=[], pasta_download=str(tmp_path))
    arquivo = tmp_path / 'sample.txt'
    arquivo.write_text('Texto qualquer sem palavra chave', encoding='utf-8')

    ok, result = scraper.analisar_arquivo(str(arquivo), '123', 'sample')

    assert ok is False
    assert result == 'palavra'
