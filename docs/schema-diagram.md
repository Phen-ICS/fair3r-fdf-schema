# FDF schema diagram

Auto-generated from `fdf_schema.json` by `tools/generate_diagram.py`. Do not edit by hand — regenerate instead.

```mermaid
flowchart TB
    classDef apiField fill:#e0f2fe,stroke:#0369a1,stroke-width:1px;
    classDef plainField fill:#f8fafc,stroke:#94a3b8,stroke-width:1px;
    classDef apiNode fill:#fef9c3,stroke:#b45309,stroke-width:1px,stroke-dasharray: 3 3;
    subgraph sec_title["Resource Description"]
        direction TB
        f_title_publication_year("publication_year<br/>type: number"):::plainField
        f_title_resource_type("resource_type<br/>type: select"):::plainField
        style sec_title fill:#1f6feb1a,stroke:#1f6feb,stroke-width:2px
    end
    subgraph sec_related_identifiers["Related Resources & References"]
        direction TB
        f_related_identifiers_related_identifier("related_identifier<br/>type: text"):::plainField
        f_related_identifiers_related_identifier_type("related_identifier_type<br/>type: select"):::plainField
        f_related_identifiers_related_relation_type("related_relation_type<br/>type: select"):::plainField
        style sec_related_identifiers fill:#6f42c11a,stroke:#6f42c1,stroke-width:2px
    end
    subgraph sec_publisher["Publisher"]
        direction TB
        f_publisher_publisher_name("publisher_name<br/>type: text"):::plainField
        f_publisher_publisher_ror("publisher_ror<br/>type: api_search<br/>ontology: ROR"):::apiField
        f_publisher_publisher_ror --> api_ror
        style sec_publisher fill:#b7791f1a,stroke:#b7791f,stroke-width:2px
    end
    subgraph sec_creators["Creators"]
        direction TB
        f_creators_role("role<br/>type: select"):::plainField
        f_creators_nameType("nameType<br/>type: select"):::plainField
        f_creators_given_name("given_name<br/>type: text"):::plainField
        f_creators_family_name("family_name<br/>type: text"):::plainField
        f_creators_organization_name("organization_name<br/>type: text"):::plainField
        f_creators_organization_ror("organization_ror<br/>type: api_search<br/>ontology: ROR"):::apiField
        f_creators_organization_ror --> api_ror
        f_creators_orcid("orcid<br/>type: api_search<br/>ontology: ORCID"):::apiField
        f_creators_orcid --> api_orcid
        f_creators_affiliation("affiliation<br/>type: api_search<br/>ontology: ROR"):::apiField
        f_creators_affiliation --> api_ror
        f_creators_contributor_roles("contributor_roles<br/>type: multi_select<br/>vocab: credit_roles"):::plainField
        style sec_creators fill:#2563eb1a,stroke:#2563eb,stroke-width:2px
    end
    subgraph sec_contributors["Contributors"]
        direction TB
        f_contributors_contributorType("contributorType<br/>type: select"):::plainField
        f_contributors_nameType("nameType<br/>type: select"):::plainField
        f_contributors_given_name("given_name<br/>type: text"):::plainField
        f_contributors_family_name("family_name<br/>type: text"):::plainField
        f_contributors_organization_name("organization_name<br/>type: text"):::plainField
        f_contributors_organization_ror("organization_ror<br/>type: api_search<br/>ontology: ROR"):::apiField
        f_contributors_organization_ror --> api_ror
        f_contributors_orcid("orcid<br/>type: api_search<br/>ontology: ORCID"):::apiField
        f_contributors_orcid --> api_orcid
        f_contributors_affiliation("affiliation<br/>type: api_search<br/>ontology: ROR"):::apiField
        f_contributors_affiliation --> api_ror
        style sec_contributors fill:#7c3aed1a,stroke:#7c3aed,stroke-width:2px
    end
    subgraph sec_organism["Biological Model"]
        direction TB
        f_organism_organism_choice("organism_choice<br/>type: preset_or_search<br/>ontology: NCBITaxon<br/>vocab: organism_presets"):::apiField
        f_organism_organism_choice --> api_ols_ncbitaxon
        f_organism_sex("sex<br/>type: preset_or_search<br/>ontology: PATO<br/>vocab: sex_presets"):::apiField
        f_organism_sex --> api_ols_pato
        style sec_organism fill:#2f855a1a,stroke:#2f855a,stroke-width:2px
    end
    subgraph sec_strain["Genetic Background / Strain"]
        direction TB
        f_strain_strain_search("strain_search<br/>type: api_search<br/>ontology: speciesBackground"):::apiField
        f_strain_strain_search --> api_ols_efo
        style sec_strain fill:#7180961a,stroke:#718096,stroke-width:2px
    end
    subgraph sec_interventions["Experimental Interventions"]
        direction TB
        f_interventions_intervention_types("intervention_types<br/>type: checkbox_group"):::plainField
        style sec_interventions fill:#0e74901a,stroke:#0e7490,stroke-width:2px
    end
    subgraph sec_genes["Involved Genes"]
        direction TB
        f_genes_cross_species_gene("cross_species_gene<br/>type: checkbox_group"):::plainField
        f_genes_gene_search("gene_search<br/>type: api_search<br/>ontology: geneAccessionId"):::apiField
        f_genes_gene_search --> api_mygene
        f_genes_transgene_origin_species("transgene_origin_species<br/>type: api_search<br/>ontology: TransgeneOrigin"):::apiField
        f_genes_transgene_origin_species --> api_ols_ncbitaxon
        f_genes_gene_chromosome_location("gene_chromosome_location<br/>type: text<br/>ontology: geneChromosomeLocation"):::plainField
        f_genes_allele_search("allele_search<br/>type: api_search<br/>ontology: alleleAccessionId"):::apiField
        f_genes_allele_search --> api_ensembl_allele
        f_genes_allele_search --> api_alliance_allele_search_mouse
        f_genes_allele_search --> api_alliance_allele_search_rat
        f_genes_allele_search --> api_alliance_allele_search_danio
        f_genes_allele_search --> api_alliance_allele_search_dmel
        f_genes_allele_search --> api_alliance_allele_search_cel
        f_genes_allele_search --> api_alliance_variant_search
        f_genes_allele_identifier_free("allele_identifier_free<br/>type: text<br/>ontology: alleleAccessionId"):::plainField
        f_genes_genetic_background("genetic_background<br/>type: api_search<br/>ontology: xenopusStrainLine"):::apiField
        f_genes_genetic_background --> api_xenbase_mutant_lines
        f_genes_xenopus_line_type("xenopus_line_type<br/>type: preset_or_search<br/>ontology: lineType<br/>vocab: xenbase_line_types"):::plainField
        f_genes_mutationType_display("mutationType_display<br/>type: text<br/>ontology: geneMutationType"):::plainField
        style sec_genes fill:#7c3aed1a,stroke:#7c3aed,stroke-width:2px
    end
    subgraph sec_chemicals["Molecules & Treatments"]
        direction TB
        f_chemicals_chem_search("chem_search<br/>type: api_search<br/>ontology: ChEBI"):::apiField
        f_chemicals_chem_search --> api_ols_chebi
        f_chemicals_treatmentprotocol("treatmentprotocol<br/>type: select"):::plainField
        f_chemicals_treatmentdesign("treatmentdesign<br/>type: text"):::plainField
        style sec_chemicals fill:#dd6b201a,stroke:#dd6b20,stroke-width:2px
    end
    subgraph sec_diet["Diet / Feeding Regiment"]
        direction TB
        f_diet_diet_search("diet_search<br/>type: api_search<br/>ontology: EFO"):::apiField
        f_diet_diet_search --> api_ols_efo_diet
        style sec_diet fill:#64748b1a,stroke:#64748b,stroke-width:2px
    end
    subgraph sec_disease["Disease Model"]
        direction TB
        f_disease_disease_search("disease_search<br/>type: api_search<br/>ontology: DOID"):::apiField
        f_disease_disease_search --> api_ols_doid
        f_disease_phenotype_search("phenotype_search<br/>type: api_search<br/>ontology: UPHENO"):::apiField
        f_disease_phenotype_search --> api_ols_upheno
        style sec_disease fill:#64748b1a,stroke:#64748b,stroke-width:2px
    end
    subgraph sec_anatomy["Tissue / Organ of Interest"]
        direction TB
        f_anatomy_anat_search("anat_search<br/>type: api_search<br/>ontology: UBERON"):::apiField
        f_anatomy_anat_search --> api_ols_uberon
        style sec_anatomy fill:#64748b1a,stroke:#64748b,stroke-width:2px
    end
    subgraph apis_group["External APIs"]
        api_alliance_allele_search_cel("Alliance Genome Allele Search (Caenorhabditis elegans)<br/>scheme: alleleAccessionId<br/>www.alliancegenome.org"):::apiNode
        api_alliance_allele_search_danio("Alliance Genome Allele Search (Danio rerio)<br/>scheme: alleleAccessionId<br/>www.alliancegenome.org"):::apiNode
        api_alliance_allele_search_dmel("Alliance Genome Allele Search (Drosophila melanogaster)<br/>scheme: alleleAccessionId<br/>www.alliancegenome.org"):::apiNode
        api_alliance_allele_search_mouse("Alliance Genome Allele Search (Mus musculus)<br/>scheme: alleleAccessionId<br/>www.alliancegenome.org"):::apiNode
        api_alliance_allele_search_rat("Rat Genome Allele Search<br/>scheme: alleleAccessionId<br/>www.alliancegenome.org"):::apiNode
        api_alliance_variant_search("Alliance Genome Variant Search<br/>scheme: alleleAccessionId<br/>www.alliancegenome.org"):::apiNode
        api_ensembl_allele("Ensembl Allele<br/>scheme: alleleAccessionId<br/>rest.ensembl.org"):::apiNode
        api_mygene("MyGene.info<br/>scheme: geneAccessionId<br/>mygene.info"):::apiNode
        api_ols_chebi("ChEBI<br/>scheme: ChEBI<br/>www.ebi.ac.uk"):::apiNode
        api_ols_doid("Disease Ontology (OLS4)<br/>scheme: DOID<br/>www.ebi.ac.uk"):::apiNode
        api_ols_efo("EFO (OLS4)<br/>scheme: EFO<br/>www.ebi.ac.uk"):::apiNode
        api_ols_efo_diet("EFO Diet (OLS4)<br/>scheme: EFO<br/>www.ebi.ac.uk"):::apiNode
        api_ols_ncbitaxon("NCBI Taxonomy (OLS4)<br/>scheme: NCBITaxon<br/>www.ebi.ac.uk"):::apiNode
        api_ols_pato("PATO (OLS4)<br/>scheme: PATO<br/>www.ebi.ac.uk"):::apiNode
        api_ols_uberon("UBERON (OLS4)<br/>scheme: UBERON<br/>www.ebi.ac.uk"):::apiNode
        api_ols_upheno("uPheno (OLS4)<br/>scheme: UPHENO<br/>www.ebi.ac.uk"):::apiNode
        api_orcid("ORCID<br/>scheme: ORCID<br/>pub.orcid.org"):::apiNode
        api_ror("ROR<br/>scheme: ROR<br/>api.ror.org"):::apiNode
        api_xenbase_mutant_lines("Xenbase Mutant Lines<br/>scheme: Strain"):::apiNode
    end
    f_genes_allele_search -.->|depends_on| f_genes_gene_search
    f_genes_allele_search -.->|pushes to| f_genes_mutationType_display
    f_genes_genetic_background -.->|depends_on| f_genes_gene_search
    f_genes_genetic_background -.->|triggers| f_genes_xenopus_line_type
    f_genes_allele_search -.->|triggers| f_genes_mutationType_display
```
