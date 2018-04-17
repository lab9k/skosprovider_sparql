from providers import SparqlProvider

if __name__ == '__main__':
    p = SparqlProvider(
        dict(sparqlEndpoint="https://qa.stad.gent/sparql", defaultGraph="http://qa.stad.gent/vocabularies"))
    result = p.get_top_concepts(language="nl", sort="label", sort_order="desc")
    print(result)
    result = p.get_all()
    print(result)
    result = p.get_by_uri("http://qa.stad.gent/id/concept/trefwoorden/0a079b8cac93345dc8fb434cf4093294")
    print(result)