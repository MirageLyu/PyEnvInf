from apyori import apriori

filepath = "package_data.csv"

def apr(filepath):
    f = open(filepath)
    lines = f.read().splitlines()
    result = list(apriori(transactions=lines))
    print(result)

apr(filepath)