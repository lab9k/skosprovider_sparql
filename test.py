from providers import SparqlProvider

if __name__ == '__main__':
    p = SparqlProvider(
        dict(sparqlEndpoint="https://qa.stad.gent/sparql", defaultGraph="http://qa.stad.gent/vocabularies"))
    result = p.get_top_concepts(language="nl", sort="label", sort_order="desc")
    print(result)
    result = p.get_all()
    print(result)
