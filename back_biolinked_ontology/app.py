from flask import Flask, jsonify, request
from flask_cors import CORS
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD, FOAF, OWL
from rdflib.plugins.sparql import prepareQuery
import requests
from datetime import datetime
import uuid
import os
import json
from decouple import config

# ============== Inicializando app para render ==============
def create_app():
    app = Flask(__name__)
    CORS(app, origins=[config('CORS_ORIGIN')], supports_credentials=True)

    # ==================== CONFIGURACIÓN RDF ====================
    graph = Graph()

    # Namespaces según la ontología
    BIOLINKED = Namespace("https://biolinked.org/ontology#")
    ENTITY = Namespace("https://biolinked.org/entity/")
    DWC = Namespace("http://rs.tdwg.org/dwc/terms/")
    SCHEMA = Namespace("http://schema.org/")
    SIGHTING = Namespace("http://biolinked.org/sighting/")

    # Bind namespaces
    for prefix, ns in [("biolinked", BIOLINKED), ("entity", ENTITY), ("dwc", DWC), 
                    ("schema", SCHEMA), ("sighting", SIGHTING),
                    ("foaf", FOAF), ("rdfs", RDFS), ("xsd", XSD), ("owl", OWL)]:
        graph.bind(prefix, ns)

    # ==================== BASE DE DATOS EN MEMORIA ====================
    especies_db = {}
    sightings_db = []

    # ==================== CARGA DE ARCHIVO RDF ====================
    def load_rdf_file(filename='biodiversity_catalog.ttl', format='turtle'):
        """Carga un archivo RDF y extrae los datos a especies_db"""
        global especies_db, sightings_db  # Agregar sightings_db
        
        print(f"Intentando cargar archivo RDF: {filename}")
        
        if not os.path.exists(filename):
            print(f"ADVERTENCIA: Archivo {filename} no encontrado.")
            return False
        
        try:
            # Cargar el grafo desde el archivo
            graph.parse(filename, format=format)
            print(f"✓ Archivo RDF cargado exitosamente: {len(graph)} tripletas")
            
            # Extraer especies del grafo
            especies_db = extract_species_from_normalized_graph()
            print(f"✓ Especies extraídas: {len(especies_db)}")
            
            # Extraer observaciones del grafo
            sightings_db = extract_sightings_from_graph()
            print(f"✓ Observaciones extraídas: {len(sightings_db)}")
            
            return True
            
        except Exception as e:
            print(f"ERROR al cargar archivo RDF: {e}")
            import traceback
            traceback.print_exc()
            return False


    def extract_species_from_normalized_graph():
        """Extrae información de especies del grafo RDF normalizado"""
        species_dict = {}
        
        # Buscar todas las especies
        query = """
        PREFIX biolinked: <https://biolinked.org/ontology#>
        PREFIX entity: <https://biolinked.org/entity/>
        
        SELECT DISTINCT ?especie
        WHERE {
            ?especie a biolinked:Especie .
        }
        """
        
        results = graph.query(query)
        
        for row in results:
            especie_uri = row.especie
            species_id = str(especie_uri).split('/')[-1].replace('especie_', '')
            
            # Extraer todos los datos de la especie
            species_data = {
                'uri': str(especie_uri)
            }
            
            # Nombre científico y común
            for s, p, o in graph.triples((especie_uri, BIOLINKED.nombreCientifico, None)):
                species_data['scientificName'] = str(o)
            
            for s, p, o in graph.triples((especie_uri, BIOLINKED.nombreComun, None)):
                species_data['commonName'] = str(o)
            
            # Descripción
            for s, p, o in graph.triples((especie_uri, BIOLINKED.descripcion, None)):
                species_data['description'] = str(o)
            
            # Extraer jerarquía taxonómica
            species_data.update(extract_taxonomy(especie_uri))
            
            # Estado de conservación
            for s, p, conservation_uri in graph.triples((especie_uri, BIOLINKED.tieneEstadoDeConservación, None)):
                for _, _, status in graph.triples((conservation_uri, BIOLINKED.estatusConservacion, None)):
                    species_data['conservationStatus'] = str(status)
            
            # Hábitats
            habitats = []
            for s, p, habitat_uri in graph.triples((especie_uri, BIOLINKED.viveEnHábitat, None)):
                for _, _, label in graph.triples((habitat_uri, RDFS.label, None)):
                    habitats.append(str(label))
            if habitats:
                species_data['habitat'] = habitats
            
            # Distribución geográfica
            distributions = []
            for s, p, dist_uri in graph.triples((especie_uri, BIOLINKED.ocurreEnDistribución, None)):
                for _, _, label in graph.triples((dist_uri, RDFS.label, None)):
                    distributions.append(str(label))
            if distributions:
                species_data['distribution'] = distributions
            
            # Características morfológicas
            morph_chars = extract_characteristics(especie_uri, BIOLINKED.tieneCaracterísticaMorfológica)
            species_data.update(morph_chars)
            
            # Características ecológicas
            eco_chars = extract_characteristics(especie_uri, BIOLINKED.tieneCaracterísticaEcológica)
            species_data.update(eco_chars)
            
            # Referencias externas
            for s, p, wikidata_uri in graph.triples((especie_uri, BIOLINKED.equivalenteEnWikidata, None)):
                species_data['wikidata'] = str(wikidata_uri).split('/')[-1]
            
            # Imagen
            for s, p, image_uri in graph.triples((especie_uri, BIOLINKED.tieneImagen, None)):
                for _, _, url in graph.triples((image_uri, BIOLINKED.url, None)):
                    species_data['image'] = str(url)
            
            species_dict[species_id] = species_data
        
        return species_dict


    def extract_taxonomy(especie_uri):
        """Extrae la jerarquía taxonómica completa"""
        taxonomy = {}
        
        # Reino
        for s, p, reino_uri in graph.triples((especie_uri, BIOLINKED.perteneceAReino, None)):
            for _, _, nombre in graph.triples((reino_uri, BIOLINKED.nombreCientifico, None)):
                taxonomy['kingdom'] = str(nombre)
        
        # Filo
        for s, p, filo_uri in graph.triples((especie_uri, BIOLINKED.perteneceAFilo, None)):
            for _, _, nombre in graph.triples((filo_uri, BIOLINKED.nombreCientifico, None)):
                taxonomy['phylum'] = str(nombre)
        
        # Clase
        for s, p, clase_uri in graph.triples((especie_uri, BIOLINKED.perteneceAClase, None)):
            for _, _, nombre in graph.triples((clase_uri, BIOLINKED.nombreCientifico, None)):
                taxonomy['class'] = str(nombre)
        
        # Orden
        for s, p, orden_uri in graph.triples((especie_uri, BIOLINKED.perteneceAOrden, None)):
            for _, _, nombre in graph.triples((orden_uri, BIOLINKED.nombreCientifico, None)):
                taxonomy['order'] = str(nombre)
        
        # Familia
        for s, p, familia_uri in graph.triples((especie_uri, BIOLINKED.perteneceAFamilia, None)):
            for _, _, nombre in graph.triples((familia_uri, BIOLINKED.nombreCientifico, None)):
                taxonomy['family'] = str(nombre)
        
        # Género
        for s, p, genero_uri in graph.triples((especie_uri, BIOLINKED.perteneceAGénero, None)):
            for _, _, nombre in graph.triples((genero_uri, BIOLINKED.nombreCientifico, None)):
                taxonomy['genus'] = str(nombre)
        
        # Especie (epíteto específico)
        if 'scientificName' in taxonomy or 'genus' in taxonomy:
            scientific_name = None
            for s, p, o in graph.triples((especie_uri, BIOLINKED.nombreCientifico, None)):
                scientific_name = str(o)
                break
            
            if scientific_name and ' ' in scientific_name:
                taxonomy['species'] = scientific_name.split()[1]
        
        return taxonomy


    def extract_characteristics(especie_uri, property_uri):
        """Extrae características morfológicas o ecológicas"""
        characteristics = {}
        
        for s, p, char_uri in graph.triples((especie_uri, property_uri, None)):
            # Obtener descripción para identificar el tipo de característica
            descripcion = None
            for _, _, desc in graph.triples((char_uri, BIOLINKED.descripcion, None)):
                descripcion = str(desc).lower()
                break
            
            # Obtener valor y unidad
            valor = None
            unidad = None
            for _, _, v in graph.triples((char_uri, BIOLINKED.valor, None)):
                valor = str(v)
            for _, _, u in graph.triples((char_uri, BIOLINKED.unidad, None)):
                unidad = str(u)
            
            if valor and descripcion:
                # Mapear según la descripción
                if 'peso' in descripcion:
                    characteristics['weight'] = f"{valor} {unidad}" if unidad else valor
                elif 'longitud' in descripcion:
                    characteristics['length'] = f"{valor} {unidad}" if unidad else valor
                elif 'altura' in descripcion:
                    characteristics['height'] = f"{valor} {unidad}" if unidad else valor
                elif 'envergadura' in descripcion:
                    characteristics['wingspan'] = f"{valor} {unidad}" if unidad else valor
                elif 'diámetro' in descripcion or 'diametro' in descripcion:
                    characteristics['diameter'] = f"{valor} {unidad}" if unidad else valor
                elif 'longevidad' in descripcion or 'esperanza de vida' in descripcion:
                    characteristics['lifespan'] = f"{valor} {unidad}" if unidad else valor
                elif 'dieta' in descripcion:
                    characteristics['diet'] = valor
        
        return characteristics


    def extract_sightings_from_graph():
        """Extrae las observaciones del grafo RDF"""
        sightings_list = []
        
        # Buscar todas las observaciones
        query = """
        PREFIX biolinked: <https://biolinked.org/ontology#>
        PREFIX sighting: <http://biolinked.org/sighting/>
        
        SELECT DISTINCT ?observacion
        WHERE {
            ?observacion a biolinked:Observacion .
        }
        """
        
        results = graph.query(query)
        
        for row in results:
            observacion_uri = row.observacion
            sighting_id = str(observacion_uri).split('/')[-1]
            
            sighting_data = {
                'id': sighting_id,
                'uri': str(observacion_uri)
            }
            
            # Extraer species_id (taxón observado)
            for s, p, especie_uri in graph.triples((observacion_uri, BIOLINKED.observaTaxón, None)):
                species_id = str(especie_uri).split('/')[-1].replace('especie_', '')
                sighting_data['species_id'] = species_id
            
            # Fecha de registro
            for s, p, fecha in graph.triples((observacion_uri, BIOLINKED.fechaRegistro, None)):
                sighting_data['created_at'] = str(fecha)
                sighting_data['date'] = str(fecha)
            
            # Descripción (location)
            for s, p, desc in graph.triples((observacion_uri, BIOLINKED.descripcion, None)):
                sighting_data['location'] = str(desc)
            
            # Coordenadas
            for s, p, lat in graph.triples((observacion_uri, BIOLINKED.latitud, None)):
                sighting_data['latitude'] = float(str(lat))
            
            for s, p, lon in graph.triples((observacion_uri, BIOLINKED.longitud, None)):
                sighting_data['longitude'] = float(str(lon))
            
            # Observador
            for s, p, persona_uri in graph.triples((observacion_uri, BIOLINKED.registradoPor, None)):
                for _, _, nombre in graph.triples((persona_uri, FOAF.name, None)):
                    sighting_data['observer'] = str(nombre)
            
            # Notas (comentarios)
            for s, p, comment in graph.triples((observacion_uri, RDFS.comment, None)):
                sighting_data['notes'] = str(comment)
            
            sightings_list.append(sighting_data)
        
        return sightings_list


    # ==================== INICIALIZACIÓN ====================
    def init_app():
        """Inicializa la aplicación cargando datos"""
        print("=" * 60)
        print("Inicializando BioLinkedCatalog API v2.0")
        print("=" * 60)
        
        # Intentar cargar archivo Turtle primero
        formats_to_try = [
            ('biodiversity_catalog.turtle', 'turtle'),
            ('biodiversity_catalog.ttl', 'turtle'),
            ('biodiversity_catalog.xml', 'xml'),
            ('biodiversity_catalog.jsonld', 'json-ld'),
            ('biodiversity_catalog.nt', 'nt'),
            ('biodiversity_catalog.n3', 'n3')
        ]
        
        loaded = False
        for filename, format_type in formats_to_try:
            if load_rdf_file(filename, format_type):
                loaded = True
                print(f"✓ Datos cargados desde: {filename}")
                break
        
        if not loaded:
            print("\n⚠ No se encontró ningún archivo RDF.")
            print("Ejecuta primero create_rdf.py para crear los datos.")
        
        print("=" * 60)
        print(f"Tripletas RDF: {len(graph)}")
        print(f"Especies registradas: {len(especies_db)}")
        print(f"Avistamientos: {len(sightings_db)}")
        print("=" * 60)

    # Inicializar al arrancar
    init_app()

    # ==================== ENDPOINTS BÁSICOS ====================
    @app.route('/')
    def home():
        """Información de la API"""
        return jsonify({
            'name': 'BioLinkedCatalog API',
            'version': '2.0',
            'description': 'API de catálogo biológico con soporte RDF completo',
            'endpoints': {
                'GET /api/health': 'Estado del servicio',
                'GET /api/species': 'Lista todas las especies',
                'GET /api/species/<id>': 'Obtiene una especie específica',
                'GET /api/search': 'Búsqueda de especies (q, class, status, kingdom)',
                'GET /api/search/advanced': 'Búsqueda avanzada (habitat, distribution, diet)',
                'GET /api/taxonomy/<level>': 'Lista valores por nivel taxonómico',
                'GET /api/taxonomy/tree': 'Árbol taxonómico completo',
                'POST /api/sparql': 'Consulta SPARQL personalizada',
                'GET /api/export/<format>': 'Exporta datos (turtle/xml/jsonld/nt/n3)',
                'GET /api/conservation': 'Especies por estado de conservación',
                'POST /api/sightings': 'Registra un avistamiento',
                'GET /api/sightings': 'Lista todos los avistamientos',
                'GET /api/stats': 'Estadísticas del catálogo',
                'GET /api/wikidata/<id>': 'Información de Wikidata',
                'GET /api/species/<id>/external-links': 'Enlaces externos de una especie',
                'POST /api/reload': 'Recarga los datos desde el archivo RDF'
            },
            'stats': {
                'total_triples': len(graph),
                'total_species': len(especies_db),
                'total_sightings': len(sightings_db)
            }
        })

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Estado del servicio"""
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'triples_count': len(graph),
            'species_count': len(especies_db),
            'sightings_count': len(sightings_db)
        })

    @app.route('/api/reload', methods=['POST'])
    def reload_data():
        """Recarga los datos desde el archivo RDF"""
        filename = request.json.get('filename', 'biodiversity_catalog.ttl') if request.json else 'biodiversity_catalog.ttl'
        format_type = request.json.get('format', 'turtle') if request.json else 'turtle'
        
        success = load_rdf_file(filename, format_type)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Datos recargados exitosamente',
                'triples': len(graph),
                'species': len(especies_db)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo cargar el archivo RDF'
            }), 400

    # ==================== ENDPOINTS DE ESPECIES ====================
    @app.route('/api/species', methods=['GET'])
    def get_all_species():
        """Obtiene todas las especies con información enriquecida"""
        return jsonify({
            'success': True,
            'count': len(especies_db),
            'species': especies_db
        })

    @app.route('/api/species/<species_id>', methods=['GET'])
    def get_species(species_id):
        """Obtiene una especie específica con todos sus datos RDF"""
        if species_id not in especies_db:
            return jsonify({'success': False, 'error': 'Especie no encontrada'}), 404
        
        # Datos básicos de la base de datos
        species_data = especies_db[species_id].copy()
        
        # Enriquecer con datos del grafo RDF
        especie_uri = ENTITY[f"especie_{species_id}"]
        
        # Obtener todas las propiedades del grafo
        rdf_properties = {}
        for s, p, o in graph.triples((especie_uri, None, None)):
            predicate = str(p).split('#')[-1].split('/')[-1]
            value = str(o)
            
            if predicate not in rdf_properties:
                rdf_properties[predicate] = []
            rdf_properties[predicate].append(value)
        
        species_data['rdf_properties'] = rdf_properties
        
        return jsonify({
            'success': True,
            'species': species_data
        })

    @app.route('/api/species/<species_id>/external-links', methods=['GET'])
    def get_external_links(species_id):
        """Genera enlaces externos para bases de datos científicas"""
        if species_id not in especies_db:
            return jsonify({'success': False, 'error': 'Especie no encontrada'}), 404
        
        species_data = especies_db[species_id]
        scientific_name = species_data.get('scientificName', '')
        
        if not scientific_name:
            return jsonify({'success': False, 'error': 'Nombre científico no disponible'}), 400
        
        links = {
            'scientificName': scientific_name,
            'wikidata': None,
            'gbif': f"https://www.gbif.org/species/search?q={scientific_name.replace(' ', '%20')}",
            'eol': f"https://eol.org/search?q={scientific_name.replace(' ', '%20')}",
            'inaturalist': f"https://www.inaturalist.org/taxa/search?q={scientific_name.replace(' ', '+')}",
            'wikipedia_es': f"https://es.wikipedia.org/wiki/{scientific_name.replace(' ', '_')}"
        }
        
        # Si tiene Wikidata, usar el ID directo
        if species_data.get('wikidata'):
            links['wikidata'] = f"https://www.wikidata.org/wiki/{species_data['wikidata']}"
        else:
            links['wikidata'] = f"https://www.wikidata.org/w/index.php?search={scientific_name.replace(' ', '+')}"
        
        return jsonify(links)


    # ==================== ENDPOINTS DE BÚSQUEDA ====================
    @app.route('/api/search', methods=['GET'])
    def search_species():
        """Búsqueda avanzada de especies con múltiples filtros"""
        query = request.args.get('q', '').lower()
        filter_class = request.args.get('class', '').lower()
        filter_status = request.args.get('status', '').lower()
        filter_kingdom = request.args.get('kingdom', '').lower()
        filter_order = request.args.get('order', '').lower()
        filter_family = request.args.get('family', '').lower()
        
        results = {}
        for species_id, data in especies_db.items():
            match = True
            
            # Búsqueda por texto
            if query:
                match = (query in data.get('scientificName', '').lower() or 
                        query in data.get('commonName', '').lower() or
                        query in data.get('family', '').lower() or
                        query in data.get('genus', '').lower() or
                        query in data.get('description', '').lower())
            
            # Filtro por clase
            if filter_class and match:
                match = filter_class in data.get('class', '').lower()
            
            # Filtro por estado de conservación
            if filter_status and match:
                match = filter_status in data.get('conservationStatus', '').lower()
            
            # Filtro por reino
            if filter_kingdom and match:
                match = filter_kingdom in data.get('kingdom', '').lower()
            
            # Filtro por orden
            if filter_order and match:
                match = filter_order in data.get('order', '').lower()
            
            # Filtro por familia
            if filter_family and match:
                match = filter_family in data.get('family', '').lower()
            
            if match:
                results[species_id] = data
        
        return jsonify({
            'success': True,
            'count': len(results),
            'results': results
        })

    @app.route('/api/search/advanced', methods=['GET'])
    def advanced_search():
        """Búsqueda avanzada por características específicas"""
        habitat_query = request.args.get('habitat', '').lower()
        distribution_query = request.args.get('distribution', '').lower()
        diet_query = request.args.get('diet', '').lower()
        
        results = {}
        for species_id, data in especies_db.items():
            match = True
            
            # Filtro por hábitat
            if habitat_query and match:
                habitats = [h.lower() for h in data.get('habitat', [])]
                match = any(habitat_query in h for h in habitats)
            
            # Filtro por distribución
            if distribution_query and match:
                distributions = [d.lower() for d in data.get('distribution', [])]
                match = any(distribution_query in d for d in distributions)
            
            # Filtro por dieta
            if diet_query and match:
                diet = data.get('diet', '').lower()
                match = diet_query in diet
            
            if match:
                results[species_id] = data
        
        return jsonify({
            'success': True,
            'count': len(results),
            'results': results
        })


    # ==================== ENDPOINTS DE TAXONOMÍA ====================
    @app.route('/api/taxonomy/<level>', methods=['GET'])
    def get_taxonomy_level(level):
        """Obtiene valores únicos por nivel taxonómico"""
        valid_levels = ['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species']
        
        if level not in valid_levels:
            return jsonify({
                'success': False,
                'error': f'Nivel no válido. Niveles válidos: {", ".join(valid_levels)}'
            }), 400
        
        values = set()
        for data in especies_db.values():
            if level in data and data[level]:
                values.add(data[level])
        
        return jsonify({
            'success': True,
            'level': level,
            'values': sorted(list(values)),
            'count': len(values)
        })


    @app.route('/api/taxonomy/tree', methods=['GET'])
    def get_taxonomy_tree():
        """Obtiene el árbol taxonómico completo organizado jerárquicamente"""
        tree = {}
        
        for species_id, data in especies_db.items():
            kingdom = data.get('kingdom', 'Unknown')
            phylum = data.get('phylum', 'Unknown')
            class_ = data.get('class', 'Unknown')
            order = data.get('order', 'Unknown')
            family = data.get('family', 'Unknown')
            genus = data.get('genus', 'Unknown')
            species = data.get('species', 'Unknown')
            
            # Construir árbol jerárquico
            if kingdom not in tree:
                tree[kingdom] = {}
            if phylum not in tree[kingdom]:
                tree[kingdom][phylum] = {}
            if class_ not in tree[kingdom][phylum]:
                tree[kingdom][phylum][class_] = {}
            if order not in tree[kingdom][phylum][class_]:
                tree[kingdom][phylum][class_][order] = {}
            if family not in tree[kingdom][phylum][class_][order]:
                tree[kingdom][phylum][class_][order][family] = {}
            if genus not in tree[kingdom][phylum][class_][order][family]:
                tree[kingdom][phylum][class_][order][family][genus] = []
            
            tree[kingdom][phylum][class_][order][family][genus].append({
                'id': species_id,
                'scientificName': data.get('scientificName', ''),
                'commonName': data.get('commonName', ''),
                'species': species
            })
        
        return jsonify({
            'success': True,
            'tree': tree
        })


    # ==================== ENDPOINTS DE CONSERVACIÓN ====================
    @app.route('/api/conservation', methods=['GET'])
    def get_conservation_status():
        """Obtiene especies agrupadas por estado de conservación"""
        by_status = {}
        
        for species_id, data in especies_db.items():
            status = data.get('conservationStatus', 'Unknown')
            if status not in by_status:
                by_status[status] = []
            
            by_status[status].append({
                'id': species_id,
                'scientificName': data.get('scientificName', ''),
                'commonName': data.get('commonName', ''),
                'class': data.get('class', '')
            })
        
        return jsonify({
            'success': True,
            'by_status': by_status,
            'summary': {status: len(species) for status, species in by_status.items()}
        })


    # ==================== ENDPOINTS DE AVISTAMIENTOS ====================
    @app.route('/api/sightings', methods=['GET', 'POST'])
    def handle_sightings():
        """Gestiona avistamientos de especies"""
        if request.method == 'GET':
            species_id = request.args.get('species_id')
            
            filtered_sightings = sightings_db
            if species_id:
                filtered_sightings = [s for s in sightings_db if s['species_id'] == species_id]
            
            return jsonify({
                'success': True,
                'count': len(filtered_sightings),
                'sightings': filtered_sightings
            })
        
        elif request.method == 'POST':
            data = request.json
            
            species_id = data.get('species_id')
            if species_id not in especies_db:
                return jsonify({
                    'success': False,
                    'error': 'Especie no encontrada'
                }), 404
            
            sighting_id = f"sighting_{uuid.uuid4().hex[:8]}"
            sighting = {
                'id': sighting_id,
                'species_id': species_id,
                'location': data.get('location'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'date': data.get('date', datetime.now().isoformat()),
                'observer': data.get('observer'),
                'notes': data.get('notes', ''),
                'created_at': datetime.now().isoformat()
            }
            
            sightings_db.append(sighting)
            
            # Agregar al grafo RDF
            sighting_uri = SIGHTING[sighting_id]
            especie_uri = ENTITY[f"especie_{species_id}"]
            
            graph.add((sighting_uri, RDF.type, BIOLINKED.Observacion))
            graph.add((sighting_uri, BIOLINKED.observaTaxón, especie_uri))
            graph.add((sighting_uri, BIOLINKED.fechaRegistro, Literal(sighting['created_at'], datatype=XSD.dateTime)))
            
            if sighting.get('location'):
                graph.add((sighting_uri, BIOLINKED.descripcion, Literal(sighting['location'])))
            
            if sighting.get('latitude') and sighting.get('longitude'):
                graph.add((sighting_uri, BIOLINKED.latitud, Literal(sighting['latitude'], datatype=XSD.decimal)))
                graph.add((sighting_uri, BIOLINKED.longitud, Literal(sighting['longitude'], datatype=XSD.decimal)))
            
            if sighting.get('observer'):
                observer_name = sighting['observer'].replace(' ', '_')
                observer_uri = ENTITY[f"persona_{observer_name.lower()}"]
                
                graph.add((observer_uri, RDF.type, BIOLINKED.Persona))
                graph.add((observer_uri, FOAF.name, Literal(sighting['observer'])))
                graph.add((sighting_uri, BIOLINKED.registradoPor, observer_uri))
            
            if sighting.get('notes'):
                graph.add((sighting_uri, RDFS.comment, Literal(sighting['notes'])))
            
            # Guardar el grafo actualizado en archivo
            try:
                output_file = 'biodiversity_catalog.ttl'
                graph.serialize(destination=output_file, format='turtle')
                print(f"✓ Avistamiento guardado en {output_file}")
            except Exception as e:
                print(f"⚠ Error al guardar en archivo: {e}")
            
            return jsonify({
                'success': True,
                'message': 'Avistamiento registrado exitosamente y guardado en archivo',
                'sighting': sighting,
                'uri': str(sighting_uri)
            }), 201


    # ==================== ENDPOINTS SPARQL Y EXPORT ====================
    @app.route('/api/sparql', methods=['POST'])
    def sparql_query():
        """Endpoint SPARQL para consultas personalizadas"""
        query = request.json.get('query', '')
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'No se proporcionó consulta SPARQL'
            }), 400
        
        try:
            # Ejecutar consulta
            results = graph.query(query)
            result_list = []
            
            # Obtener variables de la consulta
            vars_list = [str(var) for var in results.vars] if hasattr(results, 'vars') else []
            
            # Procesar resultados
            for row in results:
                row_dict = {}
                if vars_list:
                    # Si hay variables definidas (SELECT)
                    for var in vars_list:
                        value = row.get(var) if hasattr(row, 'get') else getattr(row, var, None)
                        if value is not None:
                            row_dict[var] = str(value)
                        else:
                            row_dict[var] = None
                else:
                    # Para consultas ASK o CONSTRUCT
                    row_dict = {'result': str(row)}
                
                result_list.append(row_dict)
            
            return jsonify({
                'success': True,
                'count': len(result_list),
                'variables': vars_list,
                'results': result_list,
                'query': query
            })
        except Exception as e:
            import traceback
            return jsonify({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }), 400


    @app.route('/api/export/<format>', methods=['GET'])
    def export_data(format):
        """Exporta el grafo RDF en diferentes formatos"""
        formats = {
            'turtle': 'turtle',
            'xml': 'xml',
            'jsonld': 'json-ld',
            'nt': 'nt',
            'n3': 'n3'
        }
        
        if format not in formats:
            return jsonify({
                'success': False,
                'error': f'Formato no soportado. Formatos válidos: {", ".join(formats.keys())}'
            }), 400
        
        try:
            serialized = graph.serialize(format=formats[format])
            
            # Guardar en archivo también
            filename = f'biolinked_catalog.{format}'
            with open(filename, 'wb') as f:
                f.write(serialized.encode('utf-8') if isinstance(serialized, str) else serialized)
            
            return serialized, 200, {
                'Content-Type': 'text/plain',
                'Content-Disposition': f'attachment; filename={filename}'
            }
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


    # ==================== ESTADÍSTICAS ====================
    @app.route('/api/stats', methods=['GET'])
    def get_statistics():
        """Estadísticas completas del catálogo"""
        stats = {
            'total_triples': len(graph),
            'total_species': len(especies_db),
            'total_sightings': len(sightings_db),
            'by_kingdom': {},
            'by_class': {},
            'by_order': {},
            'by_family': {},
            'by_status': {},
            'by_diet': {}
        }
        
        for data in especies_db.values():
            # Por reino
            kingdom = data.get('kingdom', 'Unknown')
            stats['by_kingdom'][kingdom] = stats['by_kingdom'].get(kingdom, 0) + 1
            
            # Por clase
            cls = data.get('class', 'Unknown')
            stats['by_class'][cls] = stats['by_class'].get(cls, 0) + 1
            
            # Por orden
            order = data.get('order', 'Unknown')
            stats['by_order'][order] = stats['by_order'].get(order, 0) + 1
            
            # Por familia
            family = data.get('family', 'Unknown')
            stats['by_family'][family] = stats['by_family'].get(family, 0) + 1
            
            # Por estado de conservación
            status = data.get('conservationStatus', 'Unknown')
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # Por dieta
            diet = data.get('diet')
            if diet:
                stats['by_diet'][diet] = stats['by_diet'].get(diet, 0) + 1
        
        return jsonify({
            'success': True,
            'stats': stats
        })


    # ==================== INTEGRACIÓN WIKIDATA ====================
    @app.route('/api/wikidata/<wikidata_id>', methods=['GET'])
    def get_wikidata_info(wikidata_id):
        """Obtiene información adicional de Wikidata"""
        url = f"https://www.wikidata.org/wiki/Special:EntityData/{wikidata_id}.json"
        
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return jsonify({
                    'success': True,
                    'data': response.json()
                })
            return jsonify({
                'success': False,
                'error': 'Entidad no encontrada en Wikidata'
            }), 404
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    
    return app


# ==================== INICIO DEL SERVIDOR ====================
if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
    
    