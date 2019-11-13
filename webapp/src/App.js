import React from 'react';
import { Icon, Placeholder, Menu, Container, Segment, List } from 'semantic-ui-react';
import Moment from 'react-moment';


class App extends React.Component {
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
      return <div>Error: {state.error.message}</div>;
    } else if (!state.isLoaded) {
      return (
        <Placeholder>
          <Placeholder.Line/>
        </Placeholder>
      );
    } else {
      return ([
        <Segment inverted attached compact size='mini'>
          <Menu inverted text compact size='large'>
            <Menu.Item>
              <Icon name="lab" size="large"/>
            </Menu.Item>
            <Menu.Item
              name='models'
              content=<b>Models</b>
              onClick={console.log}/>
            <Menu.Item
              name='experiments'
              content=<b>Experiments</b>
              onClick={console.log}/>
          </Menu>
        </Segment>,
        <Container>
        <Segment vertical>
        <List divided relaxed>
          {state.models.map(model => {
            const createdAt = new Date(model.created_at*1000);
            return (
              <List.Item>
                <List.Icon name='cube' size='large' verticalAlign='middle'/>
                <List.Content>
                  <List.Header as='a'>{model.name}</List.Header>
                  <List.Description as='a'>
                    <Moment format='lll'>{createdAt}</Moment>
                  </List.Description>
                </List.Content>
              </List.Item>
            )
          })}
        </List>
        </Segment>
        </Container>
      ]);
    }
  }
}


export default App;
