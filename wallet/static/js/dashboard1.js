$(function() {
    // 
    const request = new XMLHttpRequest();
    request.open("GET","/retrieve_data_api");

    // Callback function for when request completes
    request.onload = () => {
        const data = JSON.parse(request.responseText);
        getdata = data;
        "use strict";
        // ============================================================== 
        // Our Visitor
        // ============================================================== 

        var chart = c3.generate({
            bindto: '#visitor',
            data: {
                columns: [
                    ['Paid', getdata["Paid"]],
                    ['Received', getdata["Receive"]],
                    ['Sent', getdata["Send"]],
                    ['Top UP',getdata["Top UP"]],
                ],
                type: 'donut',
                onclick: function(d, i) { console.log("onclick", d, i); },
                onmouseover: function(d, i) { console.log("onmouseover", d, i); },
                onmouseout: function(d, i) { console.log("onmouseout", d, i); }
            },
            donut: {
                label: {
                    show: false
                },
                title: "Balance",
                width: 20,

            },

            legend: {
                hide: true
                //or hide: 'data1'
                //or hide: ['data1', 'data2']
            },
            color: {
                pattern: ['#eceff1', '#24d2b5', '#6772e5', '#20aee3']
            }
        });
    }
    request.send();
});

