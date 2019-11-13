import React from 'react';
import { Item, Message, Icon, Placeholder, Menu, Container, Segment } from 'semantic-ui-react';
import Moment from 'react-moment';


class Models extends React.Component {
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
    } else {
      return (
        <Item.Group divided>
          {state.models.map(model => {
            const createdAt = new Date(model.created_at*1000);
            return (
              <Item>
                <Item.Content verticalAlign='middle'>
                  <Item.Header as='a'>{model.name}</Item.Header>
                  <Item.Meta>
                    Created on <Moment format='ll'>{createdAt}</Moment>
                  </Item.Meta>
                </Item.Content>
              </Item>
            )
          })}
        </Item.Group>
      );
    }
  }
}

class App extends React.Component {
  state = { activeItem: 'models' }

  handleMenuItemClick = (e, {name}) => {
    this.setState({
      activeItem: name,
    });
  }

  render() {
    const state = this.state
    var content = null

    switch (state.activeItem) {
    case 'models':
      content = <Models/>
      break
    case 'experiments':
      content = <div>TODO</div>
      break
    default:
      content = null
      break
    }

    return ([
      <Segment inverted attached compact size='mini'>
        <Menu inverted text compact size='large'>
          <Menu.Item>
            <Icon name="lab" size="large"/>
          </Menu.Item>
          <Menu.Item
            name='models'
            active={state.activeItem === 'models'}
            content=<b>Models</b>
            onClick={this.handleMenuItemClick}/>
          <Menu.Item
            name='experiments'
            active={this.state.activeItem === 'experiments'}
            content=<b>Experiments</b>
            onClick={this.handleMenuItemClick}/>
        </Menu>
      </Segment>,
      <Container>
        <Segment vertical>{content}</Segment>
      </Container>
    ]);
  }
}


export default App;
