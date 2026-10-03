def normalize(text):
    text = "".join(text.split()).upper().replace("-", "").replace(".", "").replace("_", "").replace("·", "")
    return text

print(normalize("7-abc-123"))
print(repr(normalize("ROAD          WORK\nAHEAD")))