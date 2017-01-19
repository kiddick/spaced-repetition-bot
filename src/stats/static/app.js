Vue.component('stats-grid', {
  template: '#grid-template',
  props: {
    data: Array,
    columns: Array,
    filterKey: String,
    titles: Object
  },
  data: function () {
    var sortOrders = {}
    this.columns.forEach(function (key) {
      sortOrders[key] = 1
    })
    return {
      sortKey: '',
      sortOrders: sortOrders
    }
  },
  computed: {
    filteredData: function () {
      var sortKey = this.sortKey
      var filterKey = this.filterKey && this.filterKey.toLowerCase()
      var order = this.sortOrders[sortKey] || 1
      var data = this.data
      if (filterKey) {
        data = data.filter(function (row) {
          return Object.keys(row).some(function (key) {
            return String(row[key]).toLowerCase().indexOf(filterKey) > -1
          })
        })
      }
      if (sortKey) {
        data = data.slice().sort(function (a, b) {
          a = a[sortKey]
          b = b[sortKey]
          return (a === b ? 0 : a > b ? 1 : -1) * order
        })
      }
      return data
    }
  },
  filters: {
    strftime: function (timestamp) {
      return moment(timestamp * 1000).format('hh:mm - MMM Do YYYY');
    }
  },
  methods: {
    sortBy: function (key) {
      this.sortKey = key
      this.sortOrders[key] = this.sortOrders[key] * -1
    }
  }
})

var SpaceStats = new Vue({
  el: '#statsgrid',
  data: {
    searchQuery: '',
    gridColumns: ['content', 'forgot_counter', 'sdate', 'ndate', 'status'],
    gridTitles: {
      sdate: 'Start date',
      forgot_counter: 'Times forgot',
      ndate: 'Next notification',
      status: 'Status',
      content: 'Term'
    },
    gridData: []
  },
  mounted: function(){
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function() {
      if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
        Vue.set(SpaceStats, 'gridData', JSON.parse(xmlHttp.responseText).tasks);
    }
    xmlHttp.open("GET", '/api/get_tasks/' +  CHAT_ID, true);
    xmlHttp.send(null);
  }
})
