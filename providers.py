from SPARQLWrapper import SPARQLWrapper, JSON
from skosprovider.providers import VocabularyProvider
from skosprovider.skos import Concept


class SparqlProvider(VocabularyProvider):

    def __init__(self, metadata, **kwargs):
        super(SparqlProvider, self).__init__(metadata, **kwargs)
        if 'sparqlEndpoint' not in metadata:
            raise ValueError('Please provide a sparqlEndpoint in the metadata.')
        else:
            self.sparqlEndpoint = metadata['sparqlEndpoint']
        if 'defaultGraph' not in metadata:
            raise ValueError('Please provide a defaultGraph in the metadata.')
        else:
            self.defaultGraph = metadata['defaultGraph']
        self.sparql = SPARQLWrapper(self.sparqlEndpoint)
        self.sparql.addDefaultGraph(self.defaultGraph)

    def get_by_id(self, id):
        """Get all information on a concept or collection, based on id.

        Providers should assume that all id's passed are strings. If a provider
        knows that internally it uses numeric identifiers, it's up to the
        provider to do the typecasting. Generally, this should not be done by
        changing the id's themselves (eg. from int to str), but by doing the
        id comparisons in a type agnostic way.

        Since this method could be used to find both concepts and collections,
        it's assumed that there are no id collisions between concepts and
        collections.

        :rtype: :class:`skosprovider.skos.Concept` or
            :class:`skosprovider.skos.Collection` or `False` if the concept or
            collection is unknown to the provider.
        """

        pass

    def get_by_uri(self, uri):
        """Get all information on a concept or collection, based on a
        :term:`URI`.

        :rtype: :class:`skosprovider.skos.Concept` or
            :class:`skosprovider.skos.Collection` or `False` if the concept or
            collection is unknown to the provider.
        """
        pass

    def get_all(self, **kwargs):
        """Returns all concepts and collections in this provider.

            :param string language: Optional. If present, it should be a
                :term:`language-tag`. This language-tag is passed on to the
                underlying providers and used when selecting the label to display
                for each concept.
            :param string sort: Optional. If present, it should either be `id`,
                `label` or `sortlabel`. The `sortlabel` option means the providers should
                take into account any `sortLabel` if present, if not it will
                fallback to a regular label to sort on.
            :param string sort_order: Optional. What order to sort in: `asc` or
                `desc`. Defaults to `asc`

            :returns: A :class:`lst` of concepts and collections. Each of these is a dict
                with the following keys:

                * id: id within the conceptscheme
                * uri: :term:`uri` of the concept or collection
                * type: concept or collection
                * label: A label to represent the concept or collection. It is \
                    determined by looking at the `language` parameter, the default \
                    language of the provider and finally falls back to `en`.

        """
        self.sparql.setQuery("""
                    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    SELECT ?uri, ?label, ?type 
                    WHERE {
                           ?uri skos:prefLabel ?label.
                           ?uri rdf:type ?type.
                           FILTER (?type IN (skos:Collection, skos:Concept ) )
                           FILTER (langmatches(lang(?label), 'nl')) 
                    } 
                """)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.queryAndConvert()
        bindings = results["results"]["bindings"]
        r = list()
        for d in bindings:
            uri = d["uri"]["value"]
            m_type = d["type"]["value"][d["type"]["value"].index("#") + 1:].lower()
            label = d["label"]["value"]
            r.append(dict(uri=uri, type=m_type, label=label))
        return r

    def get_top_concepts(self, **kwargs):
        """
        Returns all top-level concepts in this provider.

        Top-level concepts are concepts that have no broader concepts
        themselves. They might have narrower concepts, but this is not
        mandatory.

        :param string language: Optional. If present, it should be a
            :term:`language-tag`. This language-tag is passed on to the
            underlying providers and used when selecting the label to display
            for each concept.
        :param string sort: Optional. If present, it should either be `id`,
            `label` or `sortlabel`. The `sortlabel` option means the providers should
            take into account any `sortLabel` if present, if not it will
            fallback to a regular label to sort on.
        :param string sort_order: Optional. What order to sort in: `asc` or
            `desc`. Defaults to `asc`

        :returns: A :class:`lst` of concepts, NOT collections. Each of these
            is a dict with the following keys:

            * id: id within the conceptscheme
            * uri: :term:`uri` of the concept or collection
            * type: concept or collection
            * label: A label to represent the concept or collection. It is \
                determined by looking at the `language` parameter, the default \
                language of the provider and finally falls back to `en`.

        """
        self.sparql.setQuery("""
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                SELECT *
                WHERE { ?conceptScheme skos:hasTopConcept ?concept. }
                """)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.queryAndConvert()
        bindings = results["results"]["bindings"]
        concepts = [Concept(id=1, uri=i) for i in [i["concept"]["value"] for i in bindings]]
        return concepts

    def find(self, query, **kwargs):
        """Find concepts that match a certain query.

        Currently query is expected to be a dict, so that complex queries can
        be passed. You can use this dict to search for concepts or collections
        with a certain label, with a certain type and for concepts that belong
        to a certain collection.

        .. code-block:: python

            # Find anything that has a label of church.
            provider.find({'label': 'church'})

            # Find all concepts that are a part of collection 5.
            provider.find({'type': 'concept', 'collection': {'id': 5})

            # Find all concepts, collections or children of these
            # that belong to collection 5.
            provider.find({'collection': {'id': 5, 'depth': 'all'})

            # Find anything that has a label of church.
            # Preferentially display a label in Dutch.
            provider.find({'label': 'church'}, language='nl')

        :param query: A dict that can be used to express a query. The following
            keys are permitted:

            * `label`: Search for something with this label value. An empty \
                label is equal to searching for all concepts.
            * `type`: Limit the search to certain SKOS elements. If not \
                present or `None`, `all` is assumed:

                * `concept`: Only return :class:`skosprovider.skos.Concept` \
                    instances.
                * `collection`: Only return \
                    :class:`skosprovider.skos.Collection` instances.
                * `all`: Return both :class:`skosprovider.skos.Concept` and \
                    :class:`skosprovider.skos.Collection` instances.
            * `collection`: Search only for concepts belonging to a certain \
                collection. This argument should be a dict with two keys:

                * `id`: The id of a collection. Required.
                * `depth`: Can be `members` or `all`. Optional. If not \
                    present, `members` is assumed, meaning only concepts or \
                    collections that are a direct member of the collection \
                    should be considered. When set to `all`, this method \
                    should return concepts and collections that are a member \
                    of the collection or are a narrower concept of a member \
                    of the collection.

        :param string language: Optional. If present, it should be a
            :term:`language-tag`. This language-tag is passed on to the
            underlying providers and used when selecting the label to display
            for each concept.
        :param string sort: Optional. If present, it should either be `id`,
            `label` or `sortlabel`. The `sortlabel` option means the providers should
            take into account any `sortLabel` if present, if not it will
            fallback to a regular label to sort on.
        :param string sort_order: Optional. What order to sort in: `asc` or
            `desc`. Defaults to `asc`

        :returns: A :class:`lst` of concepts and collections. Each of these
            is a dict with the following keys:

            * id: id within the conceptscheme
            * uri: :term:`uri` of the concept or collection
            * type: concept or collection
            * label: A label to represent the concept or collection. It is \
                determined by looking at the `language` parameter, the default \
                language of the provider and finally falls back to `en`.

        """

    def expand(self, id):
        """Expand a concept or collection to all it's narrower
        concepts.

        This method should recurse and also return narrower concepts
        of narrower concepts.

        If the id passed belongs to a :class:`skosprovider.skos.Concept`,
        the id of the concept itself should be include in the return value.

        If the id passed belongs to a :class:`skosprovider.skos.Collection`,
        the id of the collection itself must not be present in the return value
        In this case the return value includes all the member concepts and
        their narrower concepts.

        :param id: A concept or collection id.
        :rtype: A list of id's or `False` if the concept or collection doesn't
            exist.
        """
        pass
