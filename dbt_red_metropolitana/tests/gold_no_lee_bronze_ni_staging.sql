-- Regla de arquitectura: Gold nunca lee Bronze/Staging directamente;
-- todo dato pasa por Silver. Falla si algún modelo de gold depende de una
-- source (staging) o de un modelo de la carpeta staging.
{% set violaciones = [] %}
{% if execute %}
    {% for id, nodo in graph.nodes.items() %}
        {% if nodo.resource_type == 'model' and nodo.schema == 'gold' %}
            {% for dep in nodo.depends_on.nodes %}
                {% if dep.startswith('source.') or (dep in graph.nodes and graph.nodes[dep].fqn[1] == 'staging') %}
                    {% do violaciones.append(nodo.name ~ ' -> ' ~ dep) %}
                {% endif %}
            {% endfor %}
        {% endif %}
    {% endfor %}
{% endif %}

select '{{ violaciones | join(", ") }}' as dependencia_prohibida
where {{ violaciones | length }} > 0
