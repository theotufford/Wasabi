document.addEventListener('DOMContentLoaded', function () {
    renderPlate()
    document.querySelectorAll(".experimentTitle").forEach(title => {
        title.addEventListener("dblclick", function() {
            selected(title)
        })
    });
    document.querySelectorAll(".versionSelector").forEach(select => {
        select.addEventListener('change', function(){
            selected(select.parentElement)
        })
    })
    document.getElementById('delete').addEventListener('click', function(){
        let experiment = document.getElementsByClassName('selected')[0]
        if(window.confirm(`are you sure you want to delete '${experiment}'`)){
        console.log(`wouldve deleted ${experiment}`)
        }
    })
    document.getElementById('edit').addEventListener('click', function(){
        let experiment = document.getElementsByClassName('selected')[0]
        let version = experiment.firstElementChild.value
            
        window.parent.location = `${loadedurls['programmer']}?title=${experiment.id}&version=${version}`
    })
    let search = document.getElementById('search')
    let allTitles = Array.from(document.querySelectorAll(".experimentTitle"))
    let displayed = []
    search.addEventListener('input', function(){
        if(search.value == ""){
            allTitles.forEach(title => show(title))
        }else{
            allTitles.forEach(title => hide(title))
        }
        displayed = allTitles.filter(title => title.id.includes(search.value))
        displayed.forEach(title => {
            show(title)
        })
    })
})