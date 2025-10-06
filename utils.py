def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200):
    """
    Metni chunk'lara böler.
    - chunk_size: her parçanın uzunluğu
    - overlap: parçalar arasında tekrar eden kısım (context kaybını önler)
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        
        # Eğer son chunk ise dur
        if end >= len(text):
            break
            
        start += chunk_size - overlap
    
    return chunks