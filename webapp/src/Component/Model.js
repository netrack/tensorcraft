import React from 'react';
import { Item, Icon, Message, Placeholder } from 'semantic-ui-react';
import Moment from 'react-moment';


export default class ModelsList extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      error: null,
      isLoaded: false,
      models: []
    };
  }

  componentDidMount() {
    fetch("http://localhost:5678/models")
      .then(res => res.json())
      .then(
        (result) => {
          this.setState({
            isLoaded: true,
            models: result
          })
        },
        (error) => {
          console.log(error)
          this.setState({
            isLoaded: true,
            error: error
          });
        }
      )
  }

  render() {
    const state = this.state;
    if (state.error) {
      return (
        <Message negative>
          <Message.Header>{state.error.message}</Message.Header>
          <p>Ensure that server is alive and running.</p>
        </Message>
      );
    } else if (!state.isLoaded) {
      return (
        <Placeholder>
          <Placeholder.Header image>
            <Placeholder.Line/>
            <Placeholder.Line/>
          </Placeholder.Header>
        </Placeholder>
      );
    }

    if (state.models.length === 0) {
      return (
        <Message icon>
          <Icon name='search'/>
          <Message.Content>
            <Message.Header>There are no uploaded models yet.</Message.Header>
          Refer to the TensorCraft <a href='/'>documentation</a> to get instruction how to upload model.
          </Message.Content>
        </Message>
      );
    }

    return (
      <Item.Group divided>
        {state.models.map(model => {
          const createdAt = new Date(model.created_at*1000);
          return (
            <Item>
              <Item.Content verticalAlign='middle'>
                <Item.Header as='a'>{model.name}</Item.Header>
                <Item.Extra>
                  <Icon name='tag'/>
                  <span>{model.tag}</span>
                  <span>Created on <Moment format='ll'>{createdAt}</Moment></span>
                </Item.Extra>
              </Item.Content>
            </Item>
          )
        })}
      </Item.Group>
    );
  }
}
