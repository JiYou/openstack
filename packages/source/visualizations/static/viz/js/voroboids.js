var w = null,
    h = 450,
    mouse = [null, null],
    fill = d3.scale.linear().domain([0, 1e4]).range(["brown", "steelblue"]),
    project_colors = {};

$(function () {
  w = $("#vis").width() - 5;

  // Initialise boids.
  var boids = new Array();

  $.ajax({
    url: window.location + "?json=true",
    dataType: "json",
    success: function (data, textStatus, jqXHR) {
      $.each(data, function (index, obj) {
        var project = obj.tenant.id;
        if (!project_colors[project]) {
          project_colors[project] = "hsla(" + Math.random() * 360 + ",100%,50%,.5)";
        }
        var b = Boid(obj).position([Math.random() * w, Math.random() * h])
                         .velocity([Math.random() * 2 - 1, Math.random() * 2 - 1])
                         .maxSpeed(obj.flavor.vcpus / 2)
                         .desiredSeparation(obj.flavor.ram / 16 + 2);
        boids.push(b);
      });
      init_flocking();
    }
  });

  function init_flocking() {
    // Compute initial positions.
    var vertices = boids.map(function(boid) {
      return boid(boids);
    });

    d3.select(window).on("blur", nullGravity);

    var svg = d3.select("#vis")
      .append("svg")
        .attr("width", w)
        .attr("height", h)
        .attr("class", "PiYG");

    var circles = svg.selectAll("circle")
                  .data(vertices)
                  .enter().append("circle");

    var nodes = svg.selectAll("circle")
                .data(boids)
                .attr("r", function(boid) {return boid.get_instance().flavor.ram / 16 + 5; });

    d3.timer(function() {
      // Update boid positions.
      boids.forEach(function(boid, i) {
        if (!boid.pause()) vertices[i] = boid(boids);
      });

      // Update circle positions.
      svg.selectAll("circle")
          .data(vertices)
          .attr("transform", function(d) { return "translate(" + d + ")"; });
      svg.selectAll("circle")
         .data(boids)
         .attr("fill", function(boid) {return project_colors[boid.get_instance().tenant.id]; })
         .on("mouseover", function (boid) {
            var $this = $(this),
                instance =  boid.get_instance();
            $this.popover({
              'title': instance.name,
              'content': "<ul>"
                         + "<li><strong>Host:</strong>&nbsp;<span>" + instance["OS-EXT-SRV-ATTR:host"] + "</span></li>"
                         + "<li><strong>Project:</strong>&nbsp;<span>" + instance.tenant.name + "</span></li>"
                         + "<li><strong>User:</strong>&nbsp;<span>" + instance.user.name + "</span></li>"
                         + "<li><strong>VCPUs:</strong>&nbsp;<span>" + instance.flavor.vcpus + "</span></li>"
                         + "<li><strong>RAM:</strong>&nbsp;<span>" + instance.flavor.ram + " MB</span></li>"
                         + "</ul>",
              'trigger': "manual",
              'placement': 'top'
            }).popover("show");
            boid.pause(true);
          })
          .on("mouseout", function (boid) {
            $(this).popover("hide");
            boid.pause(false);
          });
      });
  }

  function nullGravity() {
    mouse[0] = mouse[1] = null;
  }
});
