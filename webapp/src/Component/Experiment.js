import React from 'react';
import { Item, Icon, Message, Placeholder } from 'semantic-ui-react';


export default class ExperimentsList extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      error: null,
      isLoaded: false,
      experiments: []
    };
  }

  componentDidMount() {
    fetch("http://localhost:5678/experiments")
      .then(res => res.json())
      .then(
        (result) => {
          this.setState({
            isLoaded: true,
            experiments: result
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

    if (state.experiments.length === 0) {
      return (
        <Message icon>
          <Icon name='search'/>
          <Message.Content>
            <Message.Header>There are no experiments yet.</Message.Header>
          Refer to the TensorCraft <a href='/'>documentation</a> to get instruction how to setup experiment.
          </Message.Content>
        </Message>
      );
    }

    return (
      <Item.Group divided>
        {state.experiments.map(experiment => {
          return (
            <Item>
              <Item.Content verticalAlign='middle'>
                <Item.Header as='a'>{experiment.name}</Item.Header>
                <Item.Extra>
                  <Icon name='sync alternate'/>
                  {experiment.epochs.length}
                </Item.Extra>
              </Item.Content>
            </Item>
          )
        })}
      </Item.Group>
    );
  }
}
