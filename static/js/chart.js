day_stats = [];
chartConatiner = document.getElementById("chartContainer").getContext("2d");


$.getJSON({
	url: "/api/get",
	type: "GET",
	dataType: "json",
	success: function(data){
		chart = new Chart(chartConatiner, {
			type: "line",
			data:{
				labels: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
				datasets: [{
					label: "ответы",
					data: data["all_day"],
					backgroundColor: ["rgba(76,131,160, 0.2)"],
					borderColor: ["rgba(97,138,160,1)"],
					borderWidth: 1
				}]
			},
			options: {
				scales: {
					yAxes: [{
						scaleLabel: {
							display: true,
							labelString: "ответы"
						},
						ticks: {
							beginAtZero: true
						}
					}],
					xAxes: [{
						scaleLabel: {
							display: true,
							labelString: "время"
						},
						ticks: {
							beginAtZero: true
						}
		
					}]
				}
			}	
		});
	}
})


setInterval(function () {
	$.getJSON({
		url: '/api/get',
		type: 'GET',
		dataType: 'json',
		success: function (data) {
			$("th")[0].innerHTML = "Ответов за день: " + data["day"];
			$("th")[1].innerHTML = "Всего ответов: " + data["total"];
			$("th")[2].innerHTML = "Уникальных пользователей сегодня: " + data["dailyUniqueUsers"];
			day_stats = data["all_day"]
			for(var i = 0; i < data["all_day"].length; i++){
				chart.data.datasets[0].data[i] = data["all_day"][i];
			}
			chart.update();
		}
	});
}, 1000);
