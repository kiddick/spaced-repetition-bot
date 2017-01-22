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
      return moment(timestamp * 1000).calendar();
    },
    timefromnow: function (timestamp) {
      return moment(timestamp * 1000).fromNow();
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
    gridData: [],
    activity: []
  },
  mounted: function(){
    httpGet('/api/get_activity/', function(rsp){
      renderActivityCharts(JSON.parse(rsp.responseText).activity);
    })
    httpGet('/api/get_tasks/', function(rsp){
      Vue.set(SpaceStats, 'gridData', JSON.parse(rsp.responseText).tasks);
    })
  }
})

function httpGet(url, callback){
  var xml = new XMLHttpRequest();
  xml.onreadystatechange = function() {
    if (xml.readyState == 4 && xml.status == 200){
      callback(xml);
    }
  }
  xml.open("GET", url + CHAT_ID, true);
  xml.send(null);
}

function fitToContainer(canvas) {
  canvas.style.width = '100%';
  canvas.style.height = '100%';
  canvas.width  = canvas.offsetWidth;
  canvas.height = canvas.offsetHeight;
}

function renderActivityCharts(activity){
  // composing data for charts
  var data = {
    add: [],
    forgot: [],
    remember: [],
    add_bot_total: 0,
    add_ext_total: 0
  };
  activity.forEach(function(item){
    var date = new Date(item.date * 1000);
    data.add.push({x: date, y: item.add.bot + item.add.ext});
    data.remember.push({x: date, y: item.remember});
    data.forgot.push({x: date, y: item.forgot});
    data.add_bot_total += item.add.bot;
    data.add_ext_total += item.add.ext;
  })

  var ctx = document.getElementById("newTermsChart");
  fitToContainer(ctx);
  var scatterChart = new Chart(ctx, {
    type: 'line',
    data: {
      datasets: [{
        label: 'Added terms', data: data.add,
        backgroundColor: "rgba(75, 192, 192, 0.4)",
        borderColor: "#4BC0C0"
      }]
    },
    options: {
      showTooltips: true,
      scales: {xAxes: [{type: 'time', position: 'bottom'}]}
    }
  });

  var ctx = document.getElementById("forgRemChart");
  fitToContainer(ctx);
  var scatterChart = new Chart(ctx, {
    type: 'line',
    data: {
      datasets: [{
        label: 'Forgot pressed', data: data.forgot,
        backgroundColor: "rgba(255, 99, 132, 0.4)",
        borderColor: 'rgba(255, 99, 132, 1)'
      },{
        label: 'Remember pressed', data: data.remember,
        backgroundColor: "rgba(54, 162, 235, 0.4)",
        borderColor: "rgba(54, 162, 235, 1)",
      }]
    },
    options: {
      showTooltips: true,
      scales: {xAxes: [{type: 'time', position: 'bottom'}]}
    }
  });

  var ctx = document.getElementById("addOriginsChart");
  fitToContainer(ctx);
  var myPieChart = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: ["Telegram", "Browser"],
      datasets: [{
        data: [data.add_bot_total, data.add_ext_total],
        backgroundColor: ['#36A2EB', '#51e867']
      }]
    },
    options: {}
  });
}
