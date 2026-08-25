from Bio import Entrez

Entrez.email = "daoukimarouane@gmail.com"  # NCBI asks you to identify yourself 

handle = Entrez.esearch(db="pmc", term="cancer treatment", retmax=5)
record = Entrez.read(handle)
handle.close()

print("Total results found:", record["Count"])
print("First 5 PMC IDs:", record["IdList"])