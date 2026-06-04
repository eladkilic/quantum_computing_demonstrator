




const anleitungOeffnen = function() {
    document.getElementById("end_screen").style.display = "none";
    document.getElementById("anleitung-screen").style.display = "block";
    if (typeof anleitungZurErstenSeite === "function") anleitungZurErstenSeite();
    
}

const anleitungSchliessen = function() {
    document.getElementById("end_screen").style.display = "block";
    document.getElementById("anleitung-screen").style.display = "none";
    
}


