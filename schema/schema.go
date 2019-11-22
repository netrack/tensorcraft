package schema

import (
	"github.com/graphql-go/graphql"
	"github.com/graphql-go/relay"
)

var (
	nodeDefinitions = relay.NewNodeDefinitions(relay.NodeDefinitionsConfig{
		IDFetcher: func(id string, info graphql.ResolveInfo, ctx context.Context) (interface{}, error) {
			return nil, nil
		},
		TypeResolve: func(value interface{}, info graphql.ResolveInfo) *graphql.Object {
			return nil
		},
	})

	model = graphql.NewObject(graphql.ObjectConfig{
		Name:        "Model",
		Description: "Machine-learning model",
		Fields: graphql.Fields{
			"id":          relay.GlobalIDField("Model", nil),
			"name":        &graphql.Field{Description: "The name of the model", Type: graphql.String},
			"description": &graphql.Field{Description: "The description of the model", Type: graphql.String},
		},
		Interfaces: []*graphql.Interface{
			nodeDefinitions.NodeInterface,
		},
	})
)
