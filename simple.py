# Create simple file for Molecules/Species/Observables that can be visualized 

add('molecule', 
    Diagram('name', 'site1', 
            Optional((Choice(0, 'state1', 'state2')), True), 'site2', 
            Optional((Choice(0, 'state1', 'state2')), True), 'site3', 
            Optional((Choice(0, 'state1', 'state2')), True))

)