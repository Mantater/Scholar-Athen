import re
from sentence_transformers import SentenceTransformer, util

def split_sentences(text):
    """
    Splits text into sentences using regex.
    Looks for punctuation (.?!), followed by whitespace.
    Example: "Hello world. How are you?" → ["Hello world.", "How are you?"]
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return sentences

# Load a lightweight pretrained SentenceTransformer model
# "all-MiniLM-L6-v2" is fast and good for semantic similarity
model = SentenceTransformer("all-MiniLM-L6-v2")

def encode_sentences(sentences):
    """
    Encodes a list of sentences into embeddings (dense vectors).
    convert_to_tensor=True → returns PyTorch tensors, useful for similarity math.
    """
    return model.encode(sentences, convert_to_tensor=True)

# Demo usage
if __name__ == "__main__":
    print("Loading model and encoding sample text...")
    
    sample_text = """
    Python is a widely used programming language for data science, machine learning, and web development.
    Its simplicity and readability make it a great choice for beginners.
    Many companies rely on Python for building scalable applications.
    This short sentence won't be included.
    Sentence Transformers are useful for semantic search and similarity tasks.
    """

    # Step 1: Split the text into sentences
    sentences = split_sentences(sample_text)
    print(sentences)
    print("Extracted sentences:")
    for i, s in enumerate(sentences, 1):
        print(f"{i}. {s}")

    # Step 2: Encode sentences into embeddings
    embeddings = encode_sentences(sentences)
    print("\nEmbeddings shape:", embeddings.shape)  # (num_sentences, embedding_dim)

    """
        Similarity score ranges:
        - 1.0 → identical / highly related meaning
        - 0.0 → neutral / unrelated
        - -1.0 → opposite meaning
        """

    # Step 3: Compare similarity of sentences
    # Compute similarity between all sentences
    similarity_matrix = util.pytorch_cos_sim(embeddings, embeddings)
    print("\nPairwise similarity matrix:")
    print(similarity_matrix)

    # Optional: print nicely
    threshold = 0.7
    print(f"\nSentence pairs with similarity above {threshold}:")
    for i, sent_i in enumerate(sentences):
        for j, sent_j in enumerate(sentences):
            if i != j and similarity_matrix[i, j] >= threshold:
                print(f"Sim({i+1},{j+1})={similarity_matrix[i,j]:.3f} -> '{sent_i[:30]}...' vs '{sent_j[:30]}...'")
