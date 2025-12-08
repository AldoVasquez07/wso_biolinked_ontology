<template>
  <div id="app">
    <nav class="navbar">
      <div class="container">
        <h1 class="logo">🌿 BioLinkedCatalog</h1>
        <div class="nav-links">
          <a @click="currentView = 'home'" :class="{ active: currentView === 'home' }">Inicio</a>
          <a @click="currentView = 'search'" :class="{ active: currentView === 'search' }">Buscar</a>
          <a @click="currentView = 'taxonomy'" :class="{ active: currentView === 'taxonomy' }">Taxonomía</a>
          <a @click="currentView = 'conservation'" :class="{ active: currentView === 'conservation' }">Conservación</a>
          <a @click="currentView = 'sightings'" :class="{ active: currentView === 'sightings' }">Avistamientos</a>
          <a @click="currentView = 'sparql'" :class="{ active: currentView === 'sparql' }">SPARQL</a>
        </div>
      </div>
    </nav>

    <main class="container">
      <!-- Vista de Inicio -->
      <div v-if="currentView === 'home'" class="view">
        <div class="hero">
          <h2>Catálogo Semántico de Biodiversidad</h2>
          <p>Explora especies con datos enlazados y tecnología RDF</p>
        </div>

        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-value">{{ stats.total_triples || 0 }}</div>
            <div class="stat-label">Tripletas RDF</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.total_species || 0 }}</div>
            <div class="stat-label">Especies</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.total_sightings || 0 }}</div>
            <div class="stat-label">Avistamientos</div>
          </div>
        </div>

        <div class="section">
          <h3>Estadísticas por Taxonomía</h3>
          <div class="taxonomy-stats">
            <div class="tax-stat-item" v-for="(count, name) in stats.by_kingdom" :key="name">
              <span class="tax-label">Reino {{ name }}:</span>
              <span class="tax-value">{{ count }} especies</span>
            </div>
            <div class="tax-stat-item" v-for="(count, name) in stats.by_class" :key="name">
              <span class="tax-label">Clase {{ name }}:</span>
              <span class="tax-value">{{ count }} especies</span>
            </div>
          </div>
        </div>

        <div class="section">
          <h3>Estado de Conservación</h3>
          <div class="conservation-summary">
            <div v-for="(count, status) in stats.by_status" :key="status"
              :class="['status-badge', getStatusClass(status)]">
              <span class="status-name">{{ status }}</span>
              <span class="status-count">{{ count }}</span>
            </div>
          </div>
        </div>

        <div class="section">
          <h3>Especies Destacadas</h3>

            <div class="pagination-controls">
              <span class="items-per-page-label">Mostrar:</span>
              <select v-model.number="itemsPerPage" @change="currentPage = 1" class="items-per-page-select">
                <option :value="3">3 por página</option>
                <option :value="6">6 por página</option>
                <option :value="9">9 por página</option>
              </select>
              <span class="total-items">Total: {{ Object.keys(allSpecies).length }} especies</span>
            </div>
          <div class="species-grid">
            <div v-for="(species, id) in paginatedSpecies" :key="id" class="species-card"
              @click="viewSpeciesDetail(species[0], species[1])">
              <div class="species-image" :style="{ backgroundImage: `url(${species[1].image})` }"></div>
              <div class="species-info">
                <h4>{{ species[1].commonName }}</h4>
                <p class="scientific-name">{{ species[1].scientificName }}</p>
                <span :class="['status-tag', getStatusClass(species[1].conservationStatus)]">
                  {{ species[1].conservationStatus }}
                </span>
              </div>
            </div>
          </div>

          <div v-if="totalPages > 1" class="pagination">
            <button 
              @click="previousPage" 
              :disabled="currentPage === 1"
              class="pagination-btn pagination-prev"
              :class="{ disabled: currentPage === 1 }">
              ← Anterior
            </button>
            
            <div class="pagination-numbers">
              <button
                v-for="(page, index) in pageNumbers"
                :key="index"
                @click="goToPage(page)"
                :class="['pagination-number', { 
                  active: page === currentPage,
                  dots: page === '...'
                }]"
                :disabled="page === '...'">
                {{ page }}
              </button>
            </div>
            
            <button 
              @click="nextPage" 
              :disabled="currentPage === totalPages"
              class="pagination-btn pagination-next"
              :class="{ disabled: currentPage === totalPages }">
              Siguiente →
            </button>
          </div>
        </div>
      </div>

      <!-- Vista de Búsqueda -->
      <div v-if="currentView === 'search'" class="view">
        <h2>Buscar Especies</h2>

        <div class="search-box">
          <input v-model="searchQuery" @input="performSearch" type="text"
            placeholder="Buscar por nombre científico, común, familia, género..." class="search-input" />
          <button @click="performSearch" class="btn-primary">Buscar</button>
        </div>

        <!-- Filtros Básicos -->
        <div class="filters-section">
          <h4>Filtros:</h4>
          <div class="filters-grid">
            <div class="filter-item">
              <label>Reino:</label>
              <select v-model="searchFilters.kingdom" @change="performSearch">
                <option value="">Todos</option>
                <option value="Animalia">Animalia</option>
                <option value="Plantae">Plantae</option>
              </select>
            </div>

            <div class="filter-item">
              <label>Clase:</label>
              <select v-model="searchFilters.class" @change="performSearch">
                <option value="">Todas</option>
                <option value="Mammalia">Mammalia</option>
                <option value="Aves">Aves</option>
                <option value="Pinopsida">Pinopsida</option>
              </select>
            </div>

            <div class="filter-item">
              <label>Estado de Conservación:</label>
              <select v-model="searchFilters.status" @change="performSearch">
                <option value="">Todos</option>
                <option value="Vulnerable">Vulnerable</option>
                <option value="Endangered">En Peligro</option>
                <option value="Least Concern">Preocupación Menor</option>
              </select>
            </div>

            <button @click="clearFilters" class="btn-clear">Limpiar Filtros</button>
          </div>
        </div>

        <!-- Búsqueda Avanzada -->
        <details class="advanced-search">
          <summary>Búsqueda Avanzada</summary>
          <div class="filters-grid">
            <div class="filter-item">
              <label>Hábitat:</label>
              <input v-model="advancedFilters.habitat" placeholder="ej: Sabana, Bosque, Montaña" />
            </div>

            <div class="filter-item">
              <label>Distribución:</label>
              <input v-model="advancedFilters.distribution" placeholder="ej: África, América del Norte" />
            </div>

            <div class="filter-item">
              <label>Dieta:</label>
              <input v-model="advancedFilters.diet" placeholder="ej: Carnívoro, Herbívoro" />
            </div>

            <button @click="performAdvancedSearch" class="btn-primary">
              Buscar Avanzado
            </button>
          </div>
        </details>

        <!-- Resultados -->
        <div v-if="searchResults.length > 0" class="results-section">
          <h3>Resultados ({{ searchResults.length }})</h3>
          <div class="species-grid">
            <div v-for="(result, index) in searchResults" :key="index" class="species-card"
              @click="viewSpeciesDetail(result.id, result)">
              <div class="species-image" :style="{ backgroundImage: `url(${result.image})` }"></div>
              <div class="species-info">
                <h4>{{ result.commonName }}</h4>
                <p class="scientific-name">{{ result.scientificName }}</p>
                <p class="taxonomy-info">{{ result.family }} - {{ result.class }}</p>
                <span :class="['status-tag', getStatusClass(result.conservationStatus)]">
                  {{ result.conservationStatus }}
                </span>
              </div>
            </div>
          </div>

          <div v-if="totalPages > 1" class="pagination">
  <button 
    @click="previousPage" 
    :disabled="currentPage === 1"
    class="pagination-btn pagination-prev"
    :class="{ disabled: currentPage === 1 }">
    ← Anterior
  </button>
  
  <div class="pagination-numbers">
    <button
      v-for="(page, index) in pageNumbers"
      :key="index"
      @click="goToPage(page)"
      :class="['pagination-number', { 
        active: page === currentPage,
        dots: page === '...'
      }]"
      :disabled="page === '...'">
      {{ page }}
    </button>
  </div>
  
  <button 
    @click="nextPage" 
    :disabled="currentPage === totalPages"
    class="pagination-btn pagination-next"
    :class="{ disabled: currentPage === totalPages }">
    Siguiente →
  </button>
</div>
        </div>

        <div v-else-if="searchQuery && !loading" class="no-results">
          No se encontraron especies que coincidan con "{{ searchQuery }}"
        </div>
      </div>

      <!-- Vista de Taxonomía -->
      <div v-if="currentView === 'taxonomy'" class="view">
        <h2>Explorar por Taxonomía</h2>

        <div class="taxonomy-selector">
          <button v-for="rank in taxonomicRanks" :key="rank.value" @click="loadTaxonomyRank(rank.value)"
            :class="['btn-taxonomy', { active: selectedRank === rank.value }]">
            {{ rank.label }}
          </button>
        </div>

        <div v-if="taxonomyData && taxonomyData.values && taxonomyData.values.length > 0" class="taxonomy-results">
          <h3>{{ taxonomyData.level }} ({{ taxonomyData.count }} total)</h3>
          <div class="taxonomy-list">
            <div v-for="(value, idx) in taxonomyData.values" :key="idx" class="taxonomy-item">
              {{ value }}
            </div>
          </div>
        </div>

        <!-- Árbol Taxonómico -->
        <div class="section">
          <h3>Árbol Taxonómico</h3>
          <button @click="loadTaxonomyTree" class="btn-primary">Cargar Árbol Completo</button>

          <div v-if="taxonomyTree && taxonomyTree.tree" class="tree-view">
            <div v-for="(phylaData, kingdom) in taxonomyTree.tree" :key="kingdom" class="tree-kingdom">
              <h4>Reino: {{ kingdom }}</h4>
              <div v-for="(classData, phylum) in phylaData" :key="phylum" class="tree-phylum">
                <strong>Filo: {{ phylum }}</strong>
                <div v-for="(orderData, className) in classData" :key="className" class="tree-class">
                  → Clase: {{ className }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Vista de Conservación -->
      <div v-if="currentView === 'conservation'" class="view">
        <h2>Estado de Conservación</h2>

        <div v-if="conservationData && conservationData.by_status" class="conservation-groups">
          <div v-for="(speciesList, status) in conservationData.by_status" :key="status" class="conservation-group">
            <h3 :class="['status-header', getStatusClass(status)]">
              {{ status }} ({{ speciesList.length }})
            </h3>
            <div class="species-list">
              <div v-for="species in speciesList" :key="species.id" class="conservation-item"
                @click="loadSpeciesById(species.id)">
                <span class="species-name">{{ species.scientificName }}</span>
                <span class="common-name">{{ species.commonName }}</span>
                <span class="species-class">{{ species.class }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Vista de Avistamientos -->
      <div v-if="currentView === 'sightings'" class="view">
        <h2>Avistamientos</h2>

        <button @click="showSightingForm = !showSightingForm" class="btn-primary">
          Registrar Nuevo Avistamiento
        </button>

        <!-- Formulario de Avistamiento -->
        <div v-if="showSightingForm" class="sighting-form">
          <h3>Nuevo Avistamiento</h3>
          <form @submit.prevent="submitSighting">
            <div class="form-group">
              <label>Especie:</label>
              <select v-model="newSighting.species_id" required>
                <option value="">Selecciona una especie</option>
                <option v-for="(species, id) in allSpecies" :key="id" :value="id">
                  {{ species.commonName }} ({{ species.scientificName }})
                </option>
              </select>
            </div>

            <div class="form-group">
              <label>Ubicación:</label>
              <input v-model="newSighting.location" type="text" required placeholder="Ciudad, País" />
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>Latitud:</label>
                <input v-model="newSighting.latitude" type="number" step="0.000001" placeholder="-12.0464" />
              </div>

              <div class="form-group">
                <label>Longitud:</label>
                <input v-model="newSighting.longitude" type="number" step="0.000001" placeholder="-77.0428" />
              </div>
            </div>

            <div class="form-group">
              <label>Observador:</label>
              <input v-model="newSighting.observer" type="text" required placeholder="Tu nombre" />
            </div>

            <div class="form-group">
              <label>Notas:</label>
              <textarea v-model="newSighting.notes" rows="4" placeholder="Observaciones adicionales..."></textarea>
            </div>

            <div class="form-actions">
              <button type="submit" class="btn-primary">Guardar Avistamiento</button>
              <button type="button" @click="showSightingForm = false" class="btn-secondary">
                Cancelar
              </button>
            </div>
          </form>
        </div>

        <!-- Lista de Avistamientos -->
        <div v-if="sightings.length > 0" class="sightings-list">
          <h3>Avistamientos Registrados ({{ sightings.length }})</h3>
          <div class="sighting-grid">
            <div v-for="sighting in sightings" :key="sighting.id" class="sighting-card">
              <div class="sighting-header">
                <strong>{{ getSpeciesName(sighting.species_id) }}</strong>
                <span class="sighting-date">{{ formatDate(sighting.created_at) }}</span>
              </div>
              <div class="sighting-body">
                <p><strong>Ubicación:</strong> {{ sighting.location }}</p>
                <p v-if="sighting.latitude && sighting.longitude">
                  <strong>Coordenadas:</strong> {{ sighting.latitude }}, {{ sighting.longitude }}
                </p>
                <p><strong>Observador:</strong> {{ sighting.observer }}</p>
                <p v-if="sighting.notes"><strong>Notas:</strong> {{ sighting.notes }}</p>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="no-results">
          No hay avistamientos registrados aún
        </div>
      </div>

      <!-- Vista SPARQL -->
      <div v-if="currentView === 'sparql'" class="view">
        <h2>Consultas SPARQL</h2>

        <div class="sparql-editor">
          <h4>Editor de Consultas:</h4>
          <textarea v-model="sparqlQuery" placeholder="Escribe tu consulta SPARQL aquí..."
            class="sparql-textarea"></textarea>
          <button @click="executeSparql" class="btn-primary">▶ Ejecutar Query</button>
        </div>

        <div class="sparql-examples">
          <h4>Ejemplos de Consultas:</h4>
          <div class="examples-grid">
            <button v-for="example in sparqlExamples" :key="example.name" @click="sparqlQuery = example.query"
              class="btn-example">
              {{ example.name }}
            </button>
          </div>
        </div>

        <div v-if="sparqlResults && sparqlResults.length > 0" class="sparql-results">
          <h3>Resultados ({{ sparqlResults.length }})</h3>
          <div class="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th v-for="key in Object.keys(sparqlResults[0])" :key="key">{{ key }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(result, idx) in sparqlResults" :key="idx">
                  <td v-for="key in Object.keys(result)" :key="key">{{ result[key] }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-else-if="sparqlExecuted && !loading" class="no-results">
          La consulta no devolvió resultados
        </div>
      </div>

      <!-- Loading Spinner -->
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Cargando...</p>
      </div>
    </main>

    <!-- Modal de Detalle de Especie -->
    <div v-if="selectedSpecies" class="modal" @click.self="closeSpeciesModal">
      <div class="modal-content">
        <button class="modal-close" @click="closeSpeciesModal">✕</button>

        <div class="modal-header">
          <h2>{{ selectedSpecies.commonName }}</h2>
          <p class="scientific-name">{{ selectedSpecies.scientificName }}</p>
          <span :class="['status-tag-large', getStatusClass(selectedSpecies.conservationStatus)]">
            {{ selectedSpecies.conservationStatus }}
          </span>
        </div>

        <div class="modal-image" v-if="selectedSpecies.image">
          <img :src="selectedSpecies.image" :alt="selectedSpecies.commonName" />
        </div>

        <div class="modal-body">
          <!-- Descripción -->
          <div class="detail-section" v-if="selectedSpecies.description">
            <h4>Descripción</h4>
            <p>{{ selectedSpecies.description }}</p>
          </div>

          <!-- Taxonomía -->
          <div class="detail-section">
            <h4>Clasificación Taxonómica</h4>
            <div class="taxonomy-grid">
              <div class="tax-item"><strong>Reino:</strong> {{ selectedSpecies.kingdom }}</div>
              <div class="tax-item"><strong>Filo:</strong> {{ selectedSpecies.phylum }}</div>
              <div class="tax-item"><strong>Clase:</strong> {{ selectedSpecies.class }}</div>
              <div class="tax-item"><strong>Orden:</strong> {{ selectedSpecies.order }}</div>
              <div class="tax-item"><strong>Familia:</strong> {{ selectedSpecies.family }}</div>
              <div class="tax-item"><strong>Género:</strong> {{ selectedSpecies.genus }}</div>
            </div>
          </div>

          <!-- Características -->
          <div class="detail-section">
            <h4>Características Físicas</h4>
            <div class="characteristics-grid">
              <div v-if="selectedSpecies.weight" class="char-item">
                <span class="char-label">Peso:</span>
                <span>{{ selectedSpecies.weight }}</span>
              </div>
              <div v-if="selectedSpecies.length" class="char-item">
                <span class="char-label">Longitud:</span>
                <span>{{ selectedSpecies.length }}</span>
              </div>
              <div v-if="selectedSpecies.height" class="char-item">
                <span class="char-label">Altura:</span>
                <span>{{ selectedSpecies.height }}</span>
              </div>
              <div v-if="selectedSpecies.wingspan" class="char-item">
                <span class="char-label">Envergadura:</span>
                <span>{{ selectedSpecies.wingspan }}</span>
              </div>
              <div v-if="selectedSpecies.diameter" class="char-item">
                <span class="char-label">Diámetro:</span>
                <span>{{ selectedSpecies.diameter }}</span>
              </div>
              <div v-if="selectedSpecies.lifespan" class="char-item">
                <span class="char-label">Longevidad:</span>
                <span>{{ selectedSpecies.lifespan }}</span>
              </div>
              <div v-if="selectedSpecies.diet" class="char-item">
                <span class="char-label">Dieta:</span>
                <span>{{ selectedSpecies.diet }}</span>
              </div>
            </div>
          </div>

          <!-- Distribución y Hábitat -->
          <div class="detail-section">
            <h4>Distribución y Hábitat</h4>
            <div class="distribution-info">
              <div v-if="selectedSpecies.habitat">
                <strong>Hábitat:</strong>
                <ul>
                  <li v-for="(h, idx) in selectedSpecies.habitat" :key="idx">{{ h }}</li>
                </ul>
              </div>
              <div v-if="selectedSpecies.distribution">
                <strong>Distribución Geográfica:</strong>
                <ul>
                  <li v-for="(d, idx) in selectedSpecies.distribution" :key="idx">{{ d }}</li>
                </ul>
              </div>
            </div>
          </div>

          <!-- Enlaces Externos -->
          <div class="detail-section" v-if="externalLinks">
            <h4>Enlaces Externos</h4>
            <div class="external-links">
              <a v-if="externalLinks.wikidata" :href="externalLinks.wikidata" target="_blank" class="btn-link">
                Wikidata
              </a>
              <a v-if="externalLinks.gbif" :href="externalLinks.gbif" target="_blank" class="btn-link">
                GBIF
              </a>
              <a v-if="externalLinks.eol" :href="externalLinks.eol" target="_blank" class="btn-link">
                Encyclopedia of Life
              </a>
              <a v-if="externalLinks.inaturalist" :href="externalLinks.inaturalist" target="_blank" class="btn-link">
                iNaturalist
              </a>
              <a v-if="externalLinks.wikipedia_es" :href="externalLinks.wikipedia_es" target="_blank" class="btn-link">
                Wikipedia
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="footer">
      <div class="container">
        <p>🌿 BioLinkedCatalog - Linked Data para Biodiversidad</p>
        <p>
          <strong>Exportar datos RDF:</strong>
          <a @click="exportData('turtle')">Turtle</a> |
          <a @click="exportData('xml')">RDF/XML</a> |
          <a @click="exportData('jsonld')">JSON-LD</a> |
          <a @click="exportData('nt')">N-Triples</a> |
          <a @click="exportData('n3')">N3</a>
        </p>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      apiUrl: process.env.VUE_APP_API_URL,
      currentView: 'home',
      loading: false,

      currentPage: 1,
      itemsPerPage: 6,  // Puedes ajustar este número


      // Datos
      stats: {},
      allSpecies: {},
      searchResults: [],
      taxonomyData: null,
      taxonomyTree: null,
      conservationData: null,
      sightings: [],
      sparqlResults: [],

      // Estados de UI
      selectedSpecies: null,
      externalLinks: null,
      showSightingForm: false,
      sparqlExecuted: false,

      // Búsqueda
      searchQuery: '',
      searchFilters: {
        kingdom: '',
        class: '',
        status: '',
        order: '',
        family: ''
      },
      advancedFilters: {
        habitat: '',
        distribution: '',
        diet: ''
      },

      // Taxonomía
      taxonomicRanks: [
        { value: 'kingdom', label: 'Reino' },
        { value: 'phylum', label: 'Filo' },
        { value: 'class', label: 'Clase' },
        { value: 'order', label: 'Orden' },
        { value: 'family', label: 'Familia' },
        { value: 'genus', label: 'Género' }
      ],
      selectedRank: null,

      // Avistamientos
      newSighting: {
        species_id: '',
        location: '',
        latitude: null,
        longitude: null,
        observer: '',
        notes: ''
      },

      // SPARQL
      sparqlQuery: '',
      sparqlExamples: [
  {
    name: 'Todas las especies',
    query: `PREFIX biolinked: <https://biolinked.org/ontology#>
PREFIX entity: <https://biolinked.org/entity/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?species ?scientificName ?commonName
WHERE {
  ?species a biolinked:Especie .
  ?species biolinked:nombreCientifico ?scientificName .
  ?species biolinked:nombreComun ?commonName .
}
LIMIT 10`
  },
  {
    name: 'Especies por Reino',
    query: `PREFIX biolinked: <https://biolinked.org/ontology#>
PREFIX entity: <https://biolinked.org/entity/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?species ?scientificName ?kingdomName
WHERE {
  ?species a biolinked:Especie .
  ?species biolinked:nombreCientifico ?scientificName .
  ?species biolinked:perteneceAReino ?kingdom .
  ?kingdom biolinked:nombreCientifico ?kingdomName .
}
ORDER BY ?kingdomName`
  },
  {
    name: 'Especies en Peligro',
    query: `PREFIX biolinked: <https://biolinked.org/ontology#>
PREFIX entity: <https://biolinked.org/entity/>

SELECT ?species ?scientificName ?commonName ?status
WHERE {
  ?species a biolinked:Especie .
  ?species biolinked:nombreCientifico ?scientificName .
  ?species biolinked:nombreComun ?commonName .
  ?species biolinked:tieneEstadoDeConservación ?conservationStatus .
  ?conservationStatus biolinked:estatusConservacion ?status .
  FILTER(CONTAINS(?status, "Endangered") || CONTAINS(?status, "Vulnerable"))
}`
  },
  {
    name: 'Jerarquía taxonómica completa',
    query: `PREFIX biolinked: <https://biolinked.org/ontology#>
PREFIX entity: <https://biolinked.org/entity/>

SELECT ?species ?scientificName ?kingdom ?phylum ?class ?order ?family ?genus
WHERE {
  ?species a biolinked:Especie .
  ?species biolinked:nombreCientifico ?scientificName .
  ?species biolinked:perteneceAReino ?r .
  ?species biolinked:perteneceAFilo ?p .
  ?species biolinked:perteneceAClase ?c .
  ?species biolinked:perteneceAOrden ?o .
  ?species biolinked:perteneceAFamilia ?f .
  ?species biolinked:perteneceAGénero ?g .
  
  ?r biolinked:nombreCientifico ?kingdom .
  ?p biolinked:nombreCientifico ?phylum .
  ?c biolinked:nombreCientifico ?class .
  ?o biolinked:nombreCientifico ?order .
  ?f biolinked:nombreCientifico ?family .
  ?g biolinked:nombreCientifico ?genus .
}
ORDER BY ?scientificName`
  },
  {
    name: 'Especies con sus hábitats',
    query: `PREFIX biolinked: <https://biolinked.org/ontology#>
PREFIX entity: <https://biolinked.org/entity/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?species ?scientificName ?habitatName
WHERE {
  ?species a biolinked:Especie .
  ?species biolinked:nombreCientifico ?scientificName .
  ?species biolinked:viveEnHábitat ?habitat .
  ?habitat rdfs:label ?habitatName .
}
ORDER BY ?scientificName`
  },
  {
    name: 'Especies con distribución geográfica',
    query: `PREFIX biolinked: <https://biolinked.org/ontology#>
PREFIX entity: <https://biolinked.org/entity/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?species ?scientificName ?commonName ?distribution
WHERE {
  ?species a biolinked:Especie .
  ?species biolinked:nombreCientifico ?scientificName .
  ?species biolinked:nombreComun ?commonName .
  ?species biolinked:ocurreEnDistribución ?dist .
  ?dist rdfs:label ?distribution .
}
ORDER BY ?scientificName`
  },
  {
    name: 'Características morfológicas',
    query: `PREFIX biolinked: <https://biolinked.org/ontology#>
PREFIX entity: <https://biolinked.org/entity/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?species ?scientificName ?characteristic ?valor ?unidad
WHERE {
  ?species a biolinked:Especie .
  ?species biolinked:nombreCientifico ?scientificName .
  ?species biolinked:tieneCaracterísticaMorfológica ?char .
  ?char rdfs:label ?characteristic .
  ?char biolinked:valor ?valor .
  ?char biolinked:unidad ?unidad .
}
ORDER BY ?scientificName`
  },
  {
    name: 'Especies carnívoras',
    query: `PREFIX biolinked: <https://biolinked.org/ontology#>
PREFIX entity: <https://biolinked.org/entity/>

SELECT ?species ?scientificName ?commonName ?diet
WHERE {
  ?species a biolinked:Especie .
  ?species biolinked:nombreCientifico ?scientificName .
  ?species biolinked:nombreComun ?commonName .
  ?species biolinked:tieneCaracterísticaEcológica ?ecoChar .
  ?ecoChar biolinked:valor ?diet .
  FILTER(CONTAINS(?diet, "Carnívoro"))
}`
  },
  {
    name: 'Especies con enlaces externos',
    query: `PREFIX biolinked: <https://biolinked.org/ontology#>
PREFIX entity: <https://biolinked.org/entity/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?species ?scientificName ?wikidata ?gbif ?eol
WHERE {
  ?species a biolinked:Especie .
  ?species biolinked:nombreCientifico ?scientificName .
  OPTIONAL { ?species biolinked:equivalenteEnWikidata ?wikidata }
  OPTIONAL { ?species biolinked:equivalenteEnGBIF ?gbif }
  OPTIONAL { ?species biolinked:equivalenteEnEOL ?eol }
}`
  },
  {
    name: 'Especies del orden Carnivora',
    query: `PREFIX biolinked: <https://biolinked.org/ontology#>
PREFIX entity: <https://biolinked.org/entity/>

SELECT ?species ?scientificName ?commonName ?family
WHERE {
  ?species a biolinked:Especie .
  ?species biolinked:nombreCientifico ?scientificName .
  ?species biolinked:nombreComun ?commonName .
  ?species biolinked:perteneceAOrden ?order .
  ?species biolinked:perteneceAFamilia ?fam .
  
  ?order biolinked:nombreCientifico "Carnivora" .
  ?fam biolinked:nombreCientifico ?family .
}
ORDER BY ?family ?scientificName`
  }
]
    }
  },

  mounted() {
    this.loadInitialData();
  },

  computed: {
    // Para la página de inicio
    paginatedSpecies() {
      const entries = Object.entries(this.allSpecies);
      const start = (this.currentPage - 1) * this.itemsPerPage;
      const end = start + this.itemsPerPage;
      return entries.slice(start, end);
    },
    
    totalPages() {
      return Math.ceil(Object.keys(this.allSpecies).length / this.itemsPerPage);
    },
    
    pageNumbers() {
      const pages = [];
      const maxVisible = 5; // Máximo de números de página visibles
      
      if (this.totalPages <= maxVisible) {
        // Si hay pocas páginas, mostrar todas
        for (let i = 1; i <= this.totalPages; i++) {
          pages.push(i);
        }
      } else {
        // Lógica para muchas páginas
        if (this.currentPage <= 3) {
          // Al inicio
          for (let i = 1; i <= 4; i++) pages.push(i);
          pages.push('...');
          pages.push(this.totalPages);
        } else if (this.currentPage >= this.totalPages - 2) {
          // Al final
          pages.push(1);
          pages.push('...');
          for (let i = this.totalPages - 3; i <= this.totalPages; i++) {
            pages.push(i);
          }
        } else {
          // En el medio
          pages.push(1);
          pages.push('...');
          for (let i = this.currentPage - 1; i <= this.currentPage + 1; i++) {
            pages.push(i);
          }
          pages.push('...');
          pages.push(this.totalPages);
        }
      }
      
      return pages;
    }
  },

  methods: {
    async loadInitialData() {
      await Promise.all([
        this.loadStats(),
        this.loadAllSpecies(),
        this.loadSightings()
      ]);
    },

    // ==================== CARGA DE DATOS ====================

    async loadStats() {
      try {
        const response = await fetch(`${this.apiUrl}/stats`);
        const data = await response.json();
        this.stats = data.success ? data.stats : data;
      } catch (error) {
        console.error('Error cargando estadísticas:', error);
        this.$set(this, 'stats', {});
      }
    },

    async loadAllSpecies() {
      try {
        const response = await fetch(`${this.apiUrl}/species`);
        const data = await response.json();
        this.allSpecies = data.success ? data.species : {};
      } catch (error) {
        console.error('Error cargando especies:', error);
        this.allSpecies = {};
      }
    },

    async loadSightings() {
      try {
        const response = await fetch(`${this.apiUrl}/sightings`);
        const data = await response.json();
        this.sightings = data.success ? data.sightings : [];
      } catch (error) {
        console.error('Error cargando avistamientos:', error);
        this.sightings = [];
      }
    },

    // ==================== BÚSQUEDA ====================

    async performSearch() {
      if (!this.searchQuery && !this.searchFilters.kingdom && !this.searchFilters.class && !this.searchFilters.status) {
        this.searchResults = [];
        return;
      }

      this.loading = true;
      try {
        let url = `${this.apiUrl}/search?`;
        const params = [];

        if (this.searchQuery) params.push(`q=${encodeURIComponent(this.searchQuery)}`);
        if (this.searchFilters.kingdom) params.push(`kingdom=${this.searchFilters.kingdom}`);
        if (this.searchFilters.class) params.push(`class=${this.searchFilters.class}`);
        if (this.searchFilters.status) params.push(`status=${this.searchFilters.status}`);
        if (this.searchFilters.order) params.push(`order=${this.searchFilters.order}`);
        if (this.searchFilters.family) params.push(`family=${this.searchFilters.family}`);

        url += params.join('&');

        const response = await fetch(url);
        const data = await response.json();
        this.searchResults = data.success ? Object.entries(data.results).map(([id, species]) => ({ ...species, id })) : [];
      } catch (error) {
        console.error('Error en búsqueda:', error);
        this.searchResults = [];
      } finally {
        this.loading = false;
      }
    },

    async performAdvancedSearch() {
      this.loading = true;
      try {
        let url = `${this.apiUrl}/search/advanced?`;
        const params = [];

        if (this.advancedFilters.habitat) params.push(`habitat=${encodeURIComponent(this.advancedFilters.habitat)}`);
        if (this.advancedFilters.distribution) params.push(`distribution=${encodeURIComponent(this.advancedFilters.distribution)}`);
        if (this.advancedFilters.diet) params.push(`diet=${encodeURIComponent(this.advancedFilters.diet)}`);

        url += params.join('&');

        const response = await fetch(url);
        const data = await response.json();
        this.searchResults = data.success ? Object.entries(data.results).map(([id, species]) => ({ ...species, id })) : [];
      } catch (error) {
        console.error('Error en búsqueda avanzada:', error);
        this.searchResults = [];
      } finally {
        this.loading = false;
      }
    },

    clearFilters() {
      this.searchQuery = '';
      this.searchFilters = {
        kingdom: '',
        class: '',
        status: '',
        order: '',
        family: ''
      };
      this.advancedFilters = {
        habitat: '',
        distribution: '',
        diet: ''
      };
      this.searchResults = [];
    },

    // ==================== TAXONOMÍA ====================

    async loadTaxonomyRank(rank) {
      this.selectedRank = rank;
      this.loading = true;
      try {
        const response = await fetch(`${this.apiUrl}/taxonomy/${rank}`);
        this.taxonomyData = await response.json();
      } catch (error) {
        console.error('Error cargando taxonomía:', error);
        this.taxonomyData = null;
      } finally {
        this.loading = false;
      }
    },

    async loadTaxonomyTree() {
      this.loading = true;
      try {
        const response = await fetch(`${this.apiUrl}/taxonomy/tree`);
        this.taxonomyTree = await response.json();
      } catch (error) {
        console.error('Error cargando árbol taxonómico:', error);
        this.taxonomyTree = null;
      } finally {
        this.loading = false;
      }
    },

    // ==================== CONSERVACIÓN ====================

    async loadConservationData() {
      this.loading = true;
      try {
        const response = await fetch(`${this.apiUrl}/conservation`);
        this.conservationData = await response.json();
      } catch (error) {
        console.error('Error cargando datos de conservación:', error);
        this.conservationData = null;
      } finally {
        this.loading = false;
      }
    },

    // ==================== AVISTAMIENTOS ====================

    async submitSighting() {
      try {
        const response = await fetch(`${this.apiUrl}/sightings`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.newSighting)
        });

        const data = await response.json();

        if (data.success) {
          alert('✅ Avistamiento registrado exitosamente');
          this.showSightingForm = false;
          this.newSighting = {
            species_id: '',
            location: '',
            latitude: null,
            longitude: null,
            observer: '',
            notes: ''
          };
          await this.loadSightings();
          await this.loadStats();
        } else {
          alert('❌ Error al registrar avistamiento');
        }
      } catch (error) {
        console.error('Error registrando avistamiento:', error);
        alert('❌ Error al conectar con el servidor');
      }
    },

    // ==================== SPARQL ====================

    async executeSparql() {
      if (!this.sparqlQuery.trim()) {
        alert('⚠️ Por favor ingresa una consulta SPARQL');
        return;
      }

      this.loading = true;
      this.sparqlExecuted = true;
      try {
        const response = await fetch(`${this.apiUrl}/sparql`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: this.sparqlQuery })
        });

        const data = await response.json();
        this.sparqlResults = data.success ? data.results : [];
      } catch (error) {
        console.error('Error ejecutando SPARQL:', error);
        alert('❌ Error ejecutando consulta SPARQL');
        this.sparqlResults = [];
      } finally {
        this.loading = false;
      }
    },

    // ==================== ESPECIES ====================

    async viewSpeciesDetail(speciesId, speciesData) {
      this.selectedSpecies = speciesData;
      this.externalLinks = null;

      // Cargar enlaces externos
      try {
        const response = await fetch(`${this.apiUrl}/species/${speciesId}/external-links`);
        this.externalLinks = await response.json();
      } catch (error) {
        console.error('Error cargando enlaces externos:', error);
      }
    },

    async loadSpeciesById(speciesId) {
      try {
        const response = await fetch(`${this.apiUrl}/species/${speciesId}`);
        const data = await response.json();

        if (data.success) {
          this.viewSpeciesDetail(speciesId, data.species);
        }
      } catch (error) {
        console.error('Error cargando especie:', error);
      }
    },

    closeSpeciesModal() {
      this.selectedSpecies = null;
      this.externalLinks = null;
    },

    // ==================== EXPORTACIÓN ====================

    exportData(format) {
      window.open(`${this.apiUrl}/export/${format}`, '_blank');
    },

    // ==================== UTILIDADES ====================

    getStatusClass(status) {
      const classes = {
        'Vulnerable': 'status-vulnerable',
        'Endangered': 'status-endangered',
        'Critically Endangered': 'status-critical',
        'Least Concern': 'status-safe',
        'Near Threatened': 'status-near-threatened'
      };
      return classes[status] || 'status-unknown';
    },

    getSpeciesName(speciesId) {
      const species = this.allSpecies[speciesId];
      return species ? `${species.commonName} (${species.scientificName})` : 'Especie desconocida';
    },

    formatDate(dateString) {
      if (!dateString) return 'Fecha no disponible';
      const date = new Date(dateString);
      return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    },

    goToPage(page) {
      if (page === '...' || page < 1 || page > this.totalPages) return;
      this.currentPage = page;
      // Scroll suave hacia arriba
      
    },
  
    previousPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
        
      }
    },
  
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++;
        
      }
    }
  },

  watch: {
    currentView(newView) {
      if (newView === 'conservation' && !this.conservationData) {
        this.loadConservationData();
      }
    }
  }
}
</script>

<style>
@import url('https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css');

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ==================== NAVBAR ==================== */
.navbar {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  padding: 1rem 0;
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar .container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2d3748;
  margin: 0;
}

.nav-links {
  display: flex;
  gap: 2rem;
}

.nav-links a {
  color: #4a5568;
  text-decoration: none;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.3s;
  padding: 0.5rem 1rem;
  border-radius: 8px;
}

.nav-links a:hover,
.nav-links a.active {
  color: #667eea;
  background: rgba(102, 126, 234, 0.1);
}

/* ==================== CONTAINER ==================== */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
}

main.container {
  flex: 1;
  padding-top: 2rem;
  padding-bottom: 2rem;
}

/* ==================== HERO ==================== */
.hero {
  text-align: center;
  padding: 3rem 0;
  color: white;
}

.hero h2 {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
}

.hero p {
  font-size: 1.25rem;
  opacity: 0.9;
}

/* ==================== STATS GRID ==================== */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.stat-card {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-value {
  font-size: 3rem;
  font-weight: 700;
  color: #667eea;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 1rem;
  color: #718096;
  font-weight: 500;
}

/* ==================== SECTION ==================== */
.section {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.section h3 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 1.5rem;
}

/* ==================== TAXONOMY STATS ==================== */
.taxonomy-stats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.tax-stat-item {
  padding: 1rem;
  background: #f7fafc;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.tax-label {
  font-weight: 600;
  color: #4a5568;
  display: block;
  margin-bottom: 0.25rem;
}

.tax-value {
  color: #667eea;
  font-weight: 700;
  font-size: 1.125rem;
}

/* ==================== CONSERVATION SUMMARY ==================== */
.conservation-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.status-badge {
  padding: 0.75rem 1.5rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 600;
  flex: 1;
  min-width: 150px;
}

.status-name {
  font-size: 0.875rem;
}

.status-count {
  font-size: 1.5rem;
  font-weight: 700;
}

.status-vulnerable {
  background: #fef5e7;
  color: #d97706;
  border: 2px solid #fbbf24;
}

.status-endangered {
  background: #fee;
  color: #dc2626;
  border: 2px solid #f87171;
}

.status-critical {
  background: #fce4ec;
  color: #991b1b;
  border: 2px solid #ef4444;
}

.status-safe {
  background: #ecfdf5;
  color: #059669;
  border: 2px solid #34d399;
}

.status-near-threatened {
  background: #fff7ed;
  color: #ea580c;
  border: 2px solid #fb923c;
}

.status-unknown {
  background: #f3f4f6;
  color: #6b7280;
  border: 2px solid #d1d5db;
}

/* ==================== SPECIES GRID ==================== */
.species-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.species-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s;
}

.species-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
}

.species-image {
  width: 100%;
  height: 200px;
  background-size: cover;
  background-position: center;
  background-color: #e2e8f0;
}

.species-info {
  padding: 1.25rem;
}

.species-info h4 {
  font-size: 1.125rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 0.5rem;
}

.scientific-name {
  font-style: italic;
  color: #718096;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.taxonomy-info {
  font-size: 0.75rem;
  color: #a0aec0;
  margin-bottom: 0.75rem;
}

.status-tag {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-top: 0.5rem;
}

.status-tag-large {
  display: inline-block;
  padding: 0.5rem 1.25rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 700;
}

/* ==================== VIEW ==================== */
.view {
  animation: fadeIn 0.5s;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.view h2 {
  color: white;
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 2rem;
  text-align: center;
}

/* ==================== SEARCH ==================== */
.search-box {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

.search-input {
  flex: 1;
  padding: 1rem 1.5rem;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.3s;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* ==================== BUTTONS ==================== */
.btn-primary {
  background: #667eea;
  color: white;
  padding: 1rem 2rem;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 1rem;
}

.btn-primary:hover {
  background: #5568d3;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-secondary {
  background: #e2e8f0;
  color: #4a5568;
  padding: 1rem 2rem;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-secondary:hover {
  background: #cbd5e0;
}

.btn-clear {
  background: #f56565;
  color: white;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-clear:hover {
  background: #e53e3e;
}

/* ==================== FILTERS ==================== */
.filters-section {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.filters-section h4 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 1rem;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  align-items: end;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-item label {
  font-weight: 600;
  color: #4a5568;
  font-size: 0.875rem;
}

.filter-item select,
.filter-item input {
  padding: 0.75rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s;
}

.filter-item select:focus,
.filter-item input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* ==================== ADVANCED SEARCH ==================== */
.advanced-search {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.advanced-search summary {
  font-weight: 700;
  color: #2d3748;
  cursor: pointer;
  padding: 0.5rem;
  user-select: none;
  font-size: 1.125rem;
}

.advanced-search summary:hover {
  color: #667eea;
}

.advanced-search[open] summary {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e2e8f0;
}

/* ==================== RESULTS ==================== */
.results-section {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.results-section h3 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 1.5rem;
}

.no-results {
  background: white;
  padding: 3rem;
  border-radius: 16px;
  text-align: center;
  font-size: 1.125rem;
  color: #718096;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

/* ==================== TAXONOMY ==================== */
.taxonomy-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 2rem;
}

.btn-taxonomy {
  background: white;
  color: #4a5568;
  padding: 0.75rem 1.5rem;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-taxonomy:hover {
  border-color: #667eea;
  color: #667eea;
}

.btn-taxonomy.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.taxonomy-results {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.taxonomy-results h3 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 1.5rem;
}

.taxonomy-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.taxonomy-item {
  padding: 1rem;
  background: #f7fafc;
  border-radius: 8px;
  border-left: 4px solid #667eea;
  font-weight: 500;
  color: #2d3748;
}

/* ==================== TREE VIEW ==================== */
.tree-view {
  background: #f7fafc;
  padding: 2rem;
  border-radius: 12px;
  margin-top: 1.5rem;
}

.tree-kingdom {
  margin-bottom: 2rem;
}

.tree-kingdom h4 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 1rem;
}

.tree-phylum {
  margin-left: 1.5rem;
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: white;
  border-radius: 8px;
}

.tree-phylum strong {
  color: #4a5568;
  display: block;
  margin-bottom: 0.5rem;
}

.tree-class {
  margin-left: 1.5rem;
  color: #718096;
  padding: 0.5rem 0;
}

/* ==================== CONSERVATION ==================== */
.conservation-groups {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.conservation-group {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.status-header {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  padding: 1rem;
  border-radius: 8px;
}

.species-list {
  display: grid;
  gap: 0.75rem;
}

.conservation-item {
  padding: 1rem;
  background: #f7fafc;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s;
}

.conservation-item:hover {
  background: #e2e8f0;
  transform: translateX(5px);
}

.species-name {
  font-weight: 600;
  color: #2d3748;
}

.common-name {
  color: #718096;
  font-size: 0.875rem;
}

.species-class {
  color: #667eea;
  font-weight: 500;
  font-size: 0.875rem;
}

/* ==================== SIGHTINGS ==================== */
.sighting-form {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.sighting-form h3 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  font-weight: 600;
  color: #4a5568;
  margin-bottom: 0.5rem;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.sightings-list {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.sightings-list h3 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 1.5rem;
}

.sighting-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.sighting-card {
  background: #f7fafc;
  border-radius: 12px;
  padding: 1.5rem;
  border-left: 4px solid #667eea;
}

.sighting-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e2e8f0;
}

.sighting-header strong {
  font-size: 1.125rem;
  color: #2d3748;
}

.sighting-date {
  font-size: 0.75rem;
  color: #718096;
}

.sighting-body p {
  color: #4a5568;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

/* ==================== SPARQL ==================== */
.sparql-editor {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.sparql-editor h4 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 1rem;
}

.sparql-textarea {
  width: 100%;
  min-height: 200px;
  padding: 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  resize: vertical;
  margin-bottom: 1rem;
}

.sparql-textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.sparql-examples {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.sparql-examples h4 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 1rem;
}

.examples-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.btn-example {
  background: #f7fafc;
  color: #4a5568;
  padding: 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  text-align: left;
}

.btn-example:hover {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.sparql-results {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.sparql-results h3 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 1.5rem;
}

.table-wrapper {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #f7fafc;
}

th {
  padding: 1rem;
  text-align: left;
  font-weight: 700;
  color: #2d3748;
  border-bottom: 2px solid #e2e8f0;
}

td {
  padding: 1rem;
  border-bottom: 1px solid #e2e8f0;
  color: #4a5568;
}

tbody tr:hover {
  background: #f7fafc;
}

/* ==================== MODAL ==================== */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 2rem;
  overflow-y: auto;
}

.modal-content {
  background: white;
  border-radius: 16px;
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  animation: slideUp 0.3s;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(50px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: #e2e8f0;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  font-size: 1.5rem;
  cursor: pointer;
  transition: all 0.3s;
  z-index: 10;
}

.modal-close:hover {
  background: #cbd5e0;
  transform: rotate(90deg);
}

.modal-header {
  padding: 2rem;
  border-bottom: 2px solid #e2e8f0;
}

.modal-header h2 {
  font-size: 2rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 0.5rem;
}

.modal-image {
  width: 100%;
  height: 400px;
  overflow: hidden;
}

.modal-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.modal-body {
  padding: 2rem;
}

.detail-section {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 2px solid #e2e8f0;
}

.detail-section:last-child {
  border-bottom: none;
}

.detail-section h4 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 1rem;
}

.taxonomy-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.tax-item {
  padding: 0.75rem;
  background: #f7fafc;
  border-radius: 8px;
}

.characteristics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.char-item {
  padding: 0.75rem;
  background: #f7fafc;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.char-label {
  font-weight: 600;
  color: #4a5568;
  font-size: 0.875rem;
}

.distribution-info ul {
  list-style: none;
  padding-left: 0;
  margin-top: 0.5rem;
}

.distribution-info li {
  padding: 0.5rem;
  background: #f7fafc;
  border-radius: 6px;
  margin-bottom: 0.5rem;
  padding-left: 1.5rem;
  position: relative;
}

.distribution-info li:before {
  content: "•";
  color: #667eea;
  font-weight: bold;
  position: absolute;
  left: 0.5rem;
}

.external-links {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.btn-link {
  padding: 0.75rem 1.5rem;
  background: #667eea;
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s;
  display: inline-block;
}

.btn-link:hover {
  background: #5568d3;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

/* ==================== LOADING ==================== */
.loading {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  z-index: 999;
}

.spinner {
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top: 4px solid white;
  border-radius: 50%;
  width: 60px;
  height: 60px;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.loading p {
  color: white;
  font-weight: 600;
  font-size: 1.125rem;
}

/* ==================== FOOTER ==================== */
.footer {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 2rem 0;
  text-align: center;
  margin-top: 3rem;
}

.footer p {
  color: #4a5568;
  margin-bottom: 0.5rem;
}

.footer a {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  margin: 0 0.5rem;
  cursor: pointer;
}

.footer a:hover {
  text-decoration: underline;
}

/* ==================== RESPONSIVE ==================== */
@media (max-width: 768px) {
  .nav-links {

    flex-direction: column;
    gap: 0.5rem;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .species-grid {
    grid-template-columns: 1fr;
  }

  .search-box {
    flex-direction: column;
  }

  .filters-grid {
    grid-template-columns: 1fr;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .hero h2 {
    font-size: 1.75rem;
  }

  .modal-content {
    margin: 1rem;
  }

  .taxonomy-selector {
    flex-direction: column;
  }

  .btn-taxonomy {
    width: 100%;
  }
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  margin-top: 3rem;
  padding: 2rem 0;
}

.pagination-btn {
  padding: 0.75rem 1.5rem;
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 0.875rem;
}

.pagination-btn:hover:not(.disabled) {
  background: #667eea;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.pagination-btn.disabled {
  opacity: 0.4;
  cursor: not-allowed;
  border-color: #cbd5e0;
  color: #cbd5e0;
}

.pagination-numbers {
  display: flex;
  gap: 0.5rem;
}

.pagination-number {
  min-width: 40px;
  height: 40px;
  padding: 0.5rem;
  background: white;
  color: #4a5568;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pagination-number:hover:not(.active):not(.dots) {
  border-color: #667eea;
  color: #667eea;
  transform: translateY(-2px);
}

.pagination-number.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.pagination-number.dots {
  border: none;
  background: transparent;
  cursor: default;
  pointer-events: none;
  color: #a0aec0;
}

/* Responsive */
@media (max-width: 768px) {
  .pagination {
    flex-direction: column;
    gap: 1rem;
  }
  
  .pagination-btn {
    width: 100%;
  }
  
  .pagination-numbers {
    order: -1;
  }
  
  .pagination-number {
    min-width: 35px;
    height: 35px;
    font-size: 0.875rem;
  }
}

.pagination-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  padding: 1rem 1.5rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.items-per-page-label {
  font-weight: 600;
  color: #4a5568;
  margin-right: 0.75rem;
}

.items-per-page-select {
  padding: 0.5rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-weight: 500;
  color: #2d3748;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
}

.items-per-page-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.total-items {
  color: #718096;
  font-size: 0.875rem;
  font-weight: 500;
}

@media (max-width: 768px) {
  .pagination-controls {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
}
</style>